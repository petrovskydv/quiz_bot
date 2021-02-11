import logging
import os
import random
import requests

import vk_api as vk
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType

from utils import TelegramBotHandler

logger = logging.getLogger(__name__)


def send_vk_message(event, vk_api, answer):
    vk_api.messages.send(
        user_id=event.user_id,
        message=answer,
        random_id=random.randint(1, 1000)
    )


def main():
    load_dotenv()
    vk_token = os.environ['VK_TOKEN']
    telegram_token = os.environ['TELEGRAM_TOKEN']
    telegram_chat_id = os.environ['TELEGRAM_CHAT_ID']

    logger_handler = TelegramBotHandler(telegram_token, telegram_chat_id)
    logger_handler.setLevel(logging.INFO)
    logger_handler.formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    logger.addHandler(logger_handler)

    while True:
        vk_session = vk.VkApi(token=vk_token)
        vk_api = vk_session.get_api()
        try:
            longpoll = VkLongPoll(vk_session)
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    answer = 'привет'
                    if answer is not None:
                        send_vk_message(event, vk_api, answer)
        except vk.exceptions.ApiError as e:
            logger.exception(f'VkApiError: {e}')
        except requests.exceptions.ReadTimeout as e:
            logger.exception(f'ReadTimeoutError: {e}')


if __name__ == '__main__':
    main()
