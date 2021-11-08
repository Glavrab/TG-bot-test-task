FROM python:3.9

ENV PYTHONPATH /telegram_bot_test_task

WORKDIR /telegram_bot_test_task

COPY bot /telegram_bot_test_task/bot
COPY requirements.txt /telegram_bot_test_task/
COPY project_settings.py /telegram_bot_test_task/
COPY config.json /telegram_bot_test_task

RUN apt-get update
RUN pip3 install -r /telegram_bot_test_task/requirements.txt
