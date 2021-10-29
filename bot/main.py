from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.executor import start_polling
from loguru import logger

from bot.api_utilities import (
    process_authorize_user_request,
    disable_2fa,
    enable_2fa,
    setup_2fa,
    logout,
    change_password,
)
from bot.bot_utilities import (
    show_user_data,
    create_required_sample_in_state,
    show_start_message,
    process_error_scenario,

)
from bot.constants import (
    bot,
    dp,
    MainForm,
    Dispatcher,
    Codes,
    ApiURL,
)
from bot.exceptions import TokenRefreshError, TWOFArequiredError, UserDataError


@dp.message_handler(commands='start')
@dp.callback_query_handler(state=MainForm.start)
async def process_start_command(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    """Process start command and initiate register or sign in process"""

    if isinstance(message, types.Message):
        logger.debug(f'User {message.from_user.id} has started working with bot')
        await show_start_message(bot, message)
        await MainForm.start.set()

    if isinstance(message, types.CallbackQuery):
        if message.data == 'Get back to the main page':  # For some reason keyboard doesnt appear with 1 button and
            #  callback so we keep callback the same as text on the button
            await show_start_message(bot, message)
            return
        await create_required_sample_in_state(state, message.data)
        logger.debug(f'User {message.from_user.id} has started process code: {message.data}')
        await MainForm.data_submission.set()
        await bot.send_message(message.from_user.id, 'Type your email')


@dp.message_handler(state=MainForm.data_submission)
async def process_user_data_submission(message: types.Message, state: FSMContext):
    """Process user data submission and showing login and balance info"""
    async with state.proxy() as data:
        current_task, current_index = data['current_task'], int(data['current_task']['current_index'])
        if current_index <= len(current_task['required_data']) - 1:
            data['user_info'][f'{current_task["required_data"][current_index]}'] = message.text
        data['current_task']['current_index'] += 1
        upcoming_index = data['current_task']['current_index']

    logger.debug(f'User {message.from_user.id} has submitted data for process code: {current_task["type"]}')

    if (
            upcoming_index > len(current_task['required_data']) - 2 and
            # Means that the next item in tuple
            # will be last so we can try to make a request without 2FA(which is last if it is needed)
            any(
                (current_task['type'] == Codes.SIGN_IN_USER.value,
                 current_task['type'] == Codes.PASSWORD_CHANGE.value)
            ) or
            current_task['type'] == Codes.REGISTER_USER.value and
            upcoming_index > len(current_task['required_data']) - 1
    ):
        async with state.proxy() as data:
            confirmed_data = data.keys()
            user_data = data['user_info']
        try:
            if current_task['type'] == Codes.PASSWORD_CHANGE.value:
                await change_password(state, user_data)
                await message.answer('Password was changed!')
                await show_user_data(bot, message, state)
                await MainForm.work_process.set()
                return

            elif current_task['type'] in (Codes.SIGN_IN_USER.value, Codes.REGISTER_USER.value):
                await process_authorize_user_request(
                    user_data,
                    ApiURL.REGISTER.value if current_task['type'] == Codes.REGISTER_USER.value else ApiURL.LOG_IN.value,
                    state
                )

        except TWOFArequiredError as error:
            logger.debug(
                f'2FA pin required to process code: {current_task["type"]} task for user {message.from_user.id}'
            )
            await message.answer(error.error_message)
            return

        except UserDataError as error:
            logger.debug(
                f'Unsuccessful process code: {current_task["type"]} attempt by user {message.from_user.id}.{str(error)}'
            )
            if 'log_in' not in confirmed_data:
                await process_error_scenario(bot, message, error.error_message, state)
                return
            await message.answer(f'Error occurred. {error.error_message}')
            await show_user_data(bot, message, state)
            return

        logger.debug(f'Successful authorization attempt by user {message.from_user.id}')
        await show_user_data(bot, message, state)
        await MainForm.work_process.set()
        return

    if current_index < len(current_task['required_data']) - 1:
        await message.answer(f'Type your {current_task["required_data"][upcoming_index]}')
        return


@dp.message_handler(state=MainForm.work_process)
@dp.callback_query_handler(state=MainForm.work_process)
async def process_main_menu_funcs(message: Union[types.CallbackQuery, types.Message], state: FSMContext):
    """Process every func defined in test task to be done after successful authorization"""
    async with state.proxy() as data:
        if isinstance(message, types.CallbackQuery):
            data['current_task'] = message.data
        current_task = data['current_task']

    try:

        if isinstance(message, types.CallbackQuery):
            logger.debug(f'User {message.from_user.id} has initiated process code: {message.data}')

            if message.data == Codes.DISABLE_2FA.value:
                await bot.send_message(message.from_user.id, 'Type your 2fa code')

            elif message.data == Codes.PASSWORD_CHANGE.value:
                await bot.send_message(message.from_user.id, 'Type your email')
                await create_required_sample_in_state(state, message.data)
                await MainForm.data_submission.set()

            elif message.data == Codes.ENABLE_2FA.value:
                result = await setup_2fa(state)
                await bot.send_message(
                    message.from_user.id,
                    f'Use manual key:{result["manualEntryKey"]}'
                    f' and your account name {result["account"]} to setup 2fa or '
                    f'check this QR code: {result["qrCodeSetupImageUrl"]} and send code back'
                )

            elif message.data in (Codes.LOG_OUT_FROM_CURRENT_DEVICE.value, Codes.LOG_OUT_FROM_ALL.value):
                await logout(state, message.data)
                await show_start_message(bot, message)
                await MainForm.start.set()

        if isinstance(message, types.Message):
            logger.debug(f'User {message.from_user.id} has submitted 2FA code for process code: {current_task}')

            if current_task == Codes.DISABLE_2FA.value:
                await disable_2fa(state, message.text)
                await message.answer('2FA is disabled!')
                await show_user_data(bot, message, state)
                return

            await enable_2fa(state, message.text)
            await message.answer('2FA is enabled!')
            await show_user_data(bot, message, state)

    except TokenRefreshError as error:
        logger.debug(f'Can not refresh token for user: {message.from_user.id}')
        await process_error_scenario(bot, message, str(error), state)

    except UserDataError as error:
        logger.debug(f'Something is wrong with users {message.from_user.id} data. {str(error)}')
        await bot.send_message(message.from_user.id, f'Something is wrong with your data!{error.error_message}')
        await show_user_data(bot, message, state)


async def on_shutdown(dispatcher: Dispatcher):
    """Closing redis connection on bot shutdown event"""
    logger.warning('Shutting down bot')
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    start_polling(
        dispatcher=dp,
        skip_updates=True,
        on_shutdown=on_shutdown,
    )
