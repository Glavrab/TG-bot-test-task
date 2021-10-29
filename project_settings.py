import pathlib

import ujson
from pydantic import BaseModel


class ProjectSettings(BaseModel):

    telegram_token: str
    redis_password: str

    @classmethod
    def load_project_settings_from_json_file(cls, config_path: pathlib.Path) -> 'ProjectSettings':
        """load required project settings from config.json with given path"""
        config = ujson.load(config_path.open('r'))
        return cls(
            telegram_token=config.get('token'),
            redis_password=config.get('redis_password'),
        )


settings = ProjectSettings.load_project_settings_from_json_file(pathlib.Path('config.json'))
