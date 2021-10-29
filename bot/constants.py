import enum
from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher.filters.state import State, StatesGroup

from project_settings import settings

bot = Bot(settings.telegram_token)
dp = Dispatcher(bot, storage=RedisStorage2(host='bots_redis', password=settings.redis_password))


SIGN_IN_DATA = ('login', 'password', 'capcha', 'twoFaPin')
SIGN_UP_DATA = ('email', 'password', 'userName', 'capcha')
PASSWORD_CHANGE_DATA = ('email', 'currentPassword', 'newPassword', 'twoFaPin')


@dataclass
class Currency:
    name: str
    available_balance: float


class Codes(enum.Enum):
    """Codes appearing in app"""
    SIGN_IN_USER = '98'
    REGISTER_USER = '99'
    LOG_OUT_FROM_CURRENT_DEVICE = '100'
    LOG_OUT_FROM_ALL = '101'
    AUTHORIZED_REQUEST = '102'
    TOKEN_REFRESH_REQUEST = '103'
    PASSWORD_CHANGE = '105'
    DISABLE_2FA = '106'
    ENABLE_2FA = '107'
    GET_BACK_TO_START_PAGE = '108'
    SUCCESS = '200'


class ApiURL(enum.Enum):
    """All required API urls"""
    LOG_IN = 'https://front.kcash.ru/api/fo/Login/SignIn'
    REGISTER = 'https://front.kcash.ru/api/fo/Login/SignUpCustomer'
    LOG_OUT = 'https://front.kcash.ru/api/fo/Login/Logout'
    LOG_OUT_FROM_ALL = 'https://front.kcash.ru/api/fo/Login/LogoutFromAllDevices'
    ENABLE_2FA = 'https://front.kcash.ru/api/fo/Login/Enable2Fa'
    DISABLE_2FA = 'https://front.kcash.ru/api/fo/Login/Disable2Fa'
    SETUP_2FA = 'https://front.kcash.ru/api/fo/Login/Setup2Fa'
    CHANGE_PASSWORD = 'https://front.kcash.ru/api/fo/Login/ChangePassword'
    CHECK_BALANCE = 'https://front.kcash.ru/api/fo/Account/GetUserWallets'
    REFRESH_TOKEN = 'https://front.kcash.ru/api/fo/Login/RefreshToken'
    MANAGE_2FA = 'https://front.kcash.ru/api/fo/Login/Manage2Fa'
    ACCOUNT_INFO = 'https://front.kcash.ru/api/fo/Login/GetCurrentCustomer'


class MainMenuButtons(enum.Enum):
    """Main menu buttons representing all bot fucntional"""
    CHANGE_PASSWORD = 'Change password'
    ENABLE_2FA = 'Enable 2FA'
    DISABLE_2FA = 'Disable 2FA'
    LOGOUT = 'Logout'
    LOGOUT_FROM_ALL = 'Logout from all devices'


class StartCommandProcessButtons(enum.Enum):
    """Start command process buttons"""
    LOG_IN = 'Log in'
    REGISTER = 'Register'


class MainForm(StatesGroup):
    """Main form states at the start of working with bot"""
    start = State()
    data_submission = State()
    work_process = State()


data_sample = {
    Codes.SIGN_IN_USER.value: SIGN_IN_DATA,
    Codes.REGISTER_USER.value: SIGN_UP_DATA,
    Codes.PASSWORD_CHANGE.value: PASSWORD_CHANGE_DATA,
}
