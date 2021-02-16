import logging
from logging import Handler, LogRecord

import redis
import telegram

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


def get_quiz_questions_and_answers_from_file(quiz_filepath):
    with open(quiz_filepath, 'r', encoding='KOI8-R') as my_file:
        file_contents = my_file.read()
    text_lines = file_contents.split('\n\n')

    quiz_questions_and_answers = {}
    question_text = ''
    for string in text_lines:
        if string.startswith('Вопрос') or string.startswith('\nВопрос'):
            question_text = fetch_text(string)
        elif string.startswith('Ответ'):
            answer_text = fetch_text(string)
            answer_text = answer_text.split('.')[0]
            answer_text = answer_text.split('(')[0].strip().lower()
            quiz_questions_and_answers[question_text] = answer_text

    logger.info('загрузили вопросы и ответы')
    return quiz_questions_and_answers


def fetch_text(string):
    text = string[string.find('\n', 1) + 1:]
    text = ''.join(text.split('\n'))
    return text


def fetch_correct_answer_by_user_id(user_id, quiz_questions_and_answers, db_connection):
    try:
        question = db_connection.get(user_id)
        correct_answer = quiz_questions_and_answers[question]
        return correct_answer
    except KeyError:
        return ''


def establish_connection_redis_db(redis_host, redis_port, redis_password):
    db_connection = redis.Redis(host=redis_host, port=redis_port, db=0, password=redis_password, decode_responses=True)
    return db_connection
