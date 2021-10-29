from functools import wraps
from typing import Union, Any, Callable, Awaitable, Optional

import ujson
from aiogram.dispatcher import FSMContext
from aiohttp import ClientSession

from bot.constants import ApiURL, Currency, Codes
from bot.exceptions import AuthenticationError, TokenRefreshError, TWOFArequiredError, UserDataError


def refresh_tokens_if_needed(
        access_api_func: Callable[[FSMContext, Optional[Union[str, dict[str]]]],
                                  Awaitable[Union[str, None, dict[str], tuple]]]
):
    """if token expires for some reason make a request to refresh them and try again"""
    @wraps(access_api_func)
    async def wrapper(
            state: FSMContext,
            *args,
            **kwargs,
    ) -> Union[str, None, dict[str], tuple]:
        try:
            return await access_api_func(state, *args, **kwargs)
        except AuthenticationError:
            tokens = await get_new_tokens(state)
            async with state.proxy() as data:
                data['tokens'] = tokens
            return await access_api_func(state, *args, **kwargs)

    return wrapper


async def process_authorize_user_request(
        user_data: Union[dict[str], str],
        url: str,
        state: FSMContext,
):
    """Process authorize request"""
    session = ClientSession(json_serialize=ujson.dumps)
    async with session.post(url, json=user_data) as response:
        result = await response.json(loads=ujson.loads)
        await session.close()
    await _check_response_for_error(result)
    await state.reset_data()
    async with state.proxy() as data:
        data['login_in'] = True
        data['tokens'] = dict(refreshToken=result['refreshToken'], accessToken=result['accessToken'])


@refresh_tokens_if_needed
async def setup_2fa(state: FSMContext) -> dict[str]:
    """Process set up of 2fa"""
    session = _create_authorized_session(await _get_tokens_from_state(state))
    async with session.post(ApiURL.SETUP_2FA.value) as response:
        result = await response.json(loads=ujson.loads)
        await _check_response_for_error(result)
        await session.close()
    return result


@refresh_tokens_if_needed
async def get_info_for_successful_authorization_scenario(
        state: FSMContext,
) -> tuple[list[Currency], str]:
    """Process getting all required info presented to user after successful authorization attempt"""
    session = _create_authorized_session(await _get_tokens_from_state(state))

    async with session.get(ApiURL.CHECK_BALANCE.value) as response:
        balance_results = await response.json(loads=ujson.loads)
        await _check_response_for_error(balance_results)
        balance_info = _get_required_user_balance_info(balance_results)

    async with session.get(ApiURL.ACCOUNT_INFO.value) as response:
        account_info_results = await response.json(loads=ujson.loads)
        await _check_response_for_error(account_info_results)
        username = account_info_results['userName']
        await session.close()

    return balance_info, username


@refresh_tokens_if_needed
async def logout(state: FSMContext, log_out_type_code: str):
    """Process login out from current device or all"""
    session = _create_authorized_session(await _get_tokens_from_state(state))
    async with session.post(
            url=ApiURL.LOG_OUT.value if log_out_type_code == Codes.LOG_OUT_FROM_CURRENT_DEVICE.value
            else ApiURL.LOG_OUT_FROM_ALL.value
    ) as response:
        if response.content_type == 'application/json':
            await _check_response_for_error(await response.json(loads=ujson.loads))
        await session.close()


async def get_new_tokens(state: FSMContext) -> dict[str]:
    """Process getting new access token"""
    tokens = await _get_tokens_from_state(state, all_tokens=True)
    session = _create_authorized_session(tokens['accessToken'])
    async with session.put(ApiURL.REFRESH_TOKEN.value, params={'RefreshToken': tokens['refreshToken']}) as response:
        result = await response.json(loads=ujson.loads)
        await _check_response_for_error(result, Codes.TOKEN_REFRESH_REQUEST.value)
        await session.close()
    return result


@refresh_tokens_if_needed
async def change_password(state: FSMContext, user_data: dict[str]):
    """Process changing password using current"""
    session = _create_authorized_session(await _get_tokens_from_state(state))
    async with session.post(ApiURL.CHANGE_PASSWORD.value, json=user_data) as response:
        await session.close()
    if response.content_type == 'application/json':
        await _check_response_for_error(await response.json(loads=ujson.loads))


@refresh_tokens_if_needed
async def enable_2fa(state: FSMContext, code: str):
    """Process enabling"""
    session = _create_authorized_session(await _get_tokens_from_state(state))
    async with session.post(ApiURL.ENABLE_2FA.value, params={'code': str(code)}) as response:
        if response.content_type == 'application/json':
            await _check_response_for_error(await response.json(loads=ujson.loads))
        await session.close()


@refresh_tokens_if_needed
async def disable_2fa(state: FSMContext, code: str):
    """Process disabling 2FA authentication"""
    session = _create_authorized_session(await _get_tokens_from_state(state))
    async with session.put(ApiURL.DISABLE_2FA.value, params={'code': code}) as response:
        if response.content_type == 'application/json':
            await _check_response_for_error(await response.json(loads=ujson.loads))
        await session.close()


async def _get_tokens_from_state(state: FSMContext, all_tokens: bool = False) -> Union[str, dict[str, str]]:
    """Get one ot both tokens from state"""
    async with state.proxy() as data:
        tokens = data['tokens']
    return tokens if all_tokens else tokens['accessToken']


def _create_authorized_session(access_token: str) -> ClientSession:
    """Create authorized Client Session with authorization token and required json serializer"""
    session = ClientSession(json_serialize=ujson.dumps, headers={'authorization-vbtc': access_token})
    return session


async def _check_response_for_error(
        response: dict[Any],
        request_type_code: str = Codes.AUTHORIZED_REQUEST.value,
):
    """Check if error occurred during request"""
    if 'error' in response.keys():
        error_code, error_message = response['error']['messageCode'], response['error']['message']

        if request_type_code == Codes.TOKEN_REFRESH_REQUEST.value:
            raise TokenRefreshError(error_message, error_code)

        elif response['error']['messageCode'] == 126:
            raise TWOFArequiredError(error_message, error_code)

        elif response['error']['messageCode'] == 171:
            raise AuthenticationError(error_message, error_code)

        raise UserDataError(error_message, error_code)


def _get_required_user_balance_info(response_data: dict[str: list]) -> list[Currency]:
    """Parse account info about user balance and return all currencies and their amount"""
    balance_info = []
    for wallet in response_data['wallets']:
        balance_info.append(
            Currency(
                name=wallet.get('currencyName'),
                available_balance=wallet.get('availableFunds'),
            )
        )
    return balance_info
