#Telegram bot test task

### Table of content
* [About technical details](#about-technical-details)
* [Deploy](#deploy)
* [Project's settings](#project's-settings)

## About Technical details
**Current stack**: Python 3.9+, Docker, aiogram, aiohttp(Client part to access api), redis.

##Deploy
```shell script
$ mkdir telegram_bot_test_task
$ cd telegram_bot_test_task
$ git clone https://github.com/Glavrab/telegram_bot_test_task .
$ vim .env
$ vim config.json
$ docker-compose build
$ docker-compose up
```
## Project's settings
`.env` file composition. Values appear in docker-compose.yaml

1. REDIS_PASSWORD

```shell script
REDIS_PASSWORD="REDIS_PASSWORD123"
```

`config.json` file composition. Values appear in project's settings.
```json
{
  "telegram_token": "bot_token123",
  "redis_password": "REDIS_PASSWORD123"
}
```