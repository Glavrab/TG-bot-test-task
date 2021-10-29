class TgBotError(Exception):

    def __init__(self, error_message: str, error_code: int):
        self.error_message = error_message
        self.error_code = error_code
        super(TgBotError, self).__init__(error_message, error_code)

    def __str__(self):
        return f'{self.error_message} code: {self.error_code}'


class AuthenticationError(TgBotError):
    pass


class TokenRefreshError(TgBotError):
    pass


class TWOFArequiredError(TgBotError):
    pass


class UserDataError(TgBotError):
    pass
