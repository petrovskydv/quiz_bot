import logging
import os
import random

import redis
import requests
import vk_api as vk
from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from utils import (TelegramBotHandler, get_quiz_questions_and_answers_from_file, fetch_correct_answer_by_user_id)

logger = logging.getLogger(__name__)


def send_vk_message(event, vk_api, answer, keyboard):
    vk_api.messages.send(
        peer_id=event.user_id,
        message=answer,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard()
    )


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    load_dotenv()
    vk_token = os.environ['VK_TOKEN']
    telegram_token = os.environ['TELEGRAM_TOKEN']
    telegram_chat_id = os.environ['TELEGRAM_CHAT_ID']

    logger_handler = TelegramBotHandler(telegram_token, telegram_chat_id)
    logger_handler.setLevel(logging.INFO)
    logger_handler.formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    logger.addHandler(logger_handler)

    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()  # Переход на вторую строку
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)

    quiz = get_quiz_questions_and_answers_from_file(os.environ['QUIZ_FILEPATH'])

    db_connection = redis.Redis(host=os.environ['REDIS_HOST'],
                                port=os.environ['REDIS_PORT'],
                                db=0,
                                password=os.environ['REDIS_PASSWORD'],
                                decode_responses=True)

    while True:
        vk_session = vk.VkApi(token=vk_token)
        vk_api = vk_session.get_api()

        try:
            longpoll = VkLongPoll(vk_session)
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    correct_answer = fetch_correct_answer_by_user_id(event.user_id, quiz, db_connection)
                    if event.text == 'Сдаться':
                        message_text = f'Правильный ответ: {correct_answer}.\nДля следующего вопроса нажми "Новый вопрос"'

                    elif event.text == 'Новый вопрос':
                        message_text = random.choice(list(quiz.keys()))
                        db_connection.set(event.user_id, message_text)

                    elif event.text.strip().lower() == correct_answer:
                        message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'

                    else:
                        message_text = 'Неправильно… Попробуй ещё раз'

                    if message_text:
                        send_vk_message(event, vk_api, message_text, keyboard)

        except vk.exceptions.ApiError as e:
            logger.exception(f'VkApiError: {e}')
        except requests.exceptions.ReadTimeout as e:
            logger.exception(f'ReadTimeoutError: {e}')


if __name__ == '__main__':
    main()
