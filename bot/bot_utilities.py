import itertools
from enum import EnumMeta
from typing import Optional, Any, Union

import ujson
from aiogram import Bot
from aiogram import types
from aiogram.dispatcher import FSMContext

from bot.api_utilities import get_info_for_successful_authorization_scenario
from bot.constants import (
    data_sample,
    SIGN_IN_DATA,
    SIGN_UP_DATA,
    PASSWORD_CHANGE_DATA,
    Codes,
    MainMenuButtons,
    StartCommandProcessButtons,
    MainForm,
)


def create_inline_keyboard(buttons: list[str],
                           callback_queries: Optional[tuple] = None,
                           ) -> types.InlineKeyboardMarkup:
    """Create an inline keyboard to communicate with bot."""
    if callback_queries is None:
        callback_queries = buttons.copy()

    keyboard = types.InlineKeyboardMarkup()

    for button, query in itertools.zip_longest(buttons, callback_queries):
        button_to_add = types.InlineKeyboardButton(button, callback_data=_callback_data_normalize(query))
        keyboard.add(button_to_add)
    return keyboard


def _callback_data_normalize(data: Any) -> Optional[str]:
    """Process data to appear as str in callbacks"""
    if isinstance(data, str):
        return data
    if isinstance(data, (int, float)):
        return str(data)
    if data is None:
        return None
    return ujson.dumps(data, ensure_ascii=False)


def get_all_enum_values(
        enum: EnumMeta,
) -> list[Union[str, int]]:
    """Get all enum fields values"""
    value_map = map(lambda x: getattr(x, 'value'), enum.__members__.values())
    return list(value_map)


async def process_error_scenario(
        bot: Bot,
        message: Union[types.Message, types.CallbackQuery],
        error: str,
        state: FSMContext
):
    """Process error scenario when accessing API"""
    await state.reset_data()
    await MainForm.start.set()
    await bot.send_message(
        message.from_user.id,
        f'Error occurred {error}',
        reply_markup=create_inline_keyboard(['Get back to the main page'])
    )


async def show_start_message(bot: Bot, message: Union[types.CallbackQuery, types.Message]):
    """Show start command message"""
    await bot.send_message(
        message.from_user.id,
        'Welcome! Do you want to register or log in?',
        reply_markup=create_inline_keyboard(
            get_all_enum_values(StartCommandProcessButtons),
            callback_queries=(Codes.SIGN_IN_USER.value, Codes.REGISTER_USER.value),
        )
    )


async def create_required_sample_in_state(state: FSMContext, task_type_code: str):
    """Process creating data sample in state"""
    required_data = data_sample[task_type_code]
    async with state.proxy() as data:
        data['current_task'] = dict(
            type=task_type_code,
            current_index=0,
            required_data=required_data,
        )
        if required_data == SIGN_IN_DATA:
            data['user_info'] = dict(
                login='',
                password='',
                capcha='',
                twoFaPin='',
            )
        elif required_data == SIGN_UP_DATA:
            data['user_info'] = dict(
                email='',
                password='',
                login='',
                capcha='',
            )
        elif required_data == PASSWORD_CHANGE_DATA:
            data['user_info'] = dict(
                email='',
                currentPassword='',
                newPassword='',
                twoFaPin='',
            )


async def show_user_data(bot: Bot, message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    """Show all user data"""
    balance_info, user_name = await get_info_for_successful_authorization_scenario(state)
    user_balance_info = ''
    for currency in balance_info:
        user_balance_info += f'\n{currency.name}--balance:{currency.available_balance}'
    await bot.send_message(
        message.from_user.id,
        f'{user_name}\n\n' + user_balance_info,
        reply_markup=create_inline_keyboard(
            get_all_enum_values(MainMenuButtons),
            callback_queries=(
                Codes.PASSWORD_CHANGE.value,
                Codes.ENABLE_2FA.value,
                Codes.DISABLE_2FA.value,
                Codes.LOG_OUT_FROM_CURRENT_DEVICE.value,
                Codes.LOG_OUT_FROM_ALL.value,
            )
        )
    )


