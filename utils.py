import logging
from logging import Handler, LogRecord

import telegram

from redis_db import db_connection

logger = logging.getLogger(__name__)


class TelegramBotHandler(Handler):
    def __init__(self, token: str, chat_id: str):
        super().__init__()
        self.token = token
        self.chat_id = chat_id

    def emit(self, record: LogRecord):
        logger_bot = telegram.Bot(token=self.token)
        logger_bot.send_message(
            self.chat_id,
            self.format(record)
        )


def get_quiz_questions_and_answers_from_file():
    with open('quiz-questions/1vs1200.txt', 'r', encoding='KOI8-R') as my_file:
        file_contents = my_file.read()
    text_lines = file_contents.split('\n')
    quiz_questions_and_answers = {}
    is_question = False
    is_answer = False
    question_text = ''
    answer_text = ''
    for string in text_lines:
        if string.startswith('Вопрос'):
            is_question = True
            continue
        elif len(string) == 0 and is_answer:
            answer_text = answer_text.split('.')[0]
            answer_text = answer_text.split('(')[0].strip()
            quiz_questions_and_answers[question_text] = answer_text
            question_text = ''
            answer_text = ''
            is_answer = False
            continue
        elif len(string) == 0:
            is_question = False
            continue
        elif string.startswith('Ответ'):
            is_answer = True
            continue

        if is_question:
            question_text = ' '.join([question_text, string])
        if is_answer:
            answer_text = ' '.join([answer_text, string.strip()])
    logger.info('загрузили вопросы и ответы')
    return quiz_questions_and_answers


def fetch_correct_answer_by_user_id(update, quiz_questions_and_answers):
    question = db_connection.get(update.message.from_user["id"])
    correct_answer = quiz_questions_and_answers[question]
    return correct_answer
