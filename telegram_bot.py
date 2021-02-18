import logging
import os
import random

import redis
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler

from utils import (TelegramBotHandler, get_quiz_questions_and_answers_from_file, fetch_correct_answer_by_user_id)

logger = logging.getLogger(__name__)


def start(bot, update):
    """Send a message when the command /start is issued."""
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        'Привет! Я бот для викторин.\nНажмите "Новый вопрос" для начала викторины.\n/cancel - для отмены.',
        reply_markup=reply_markup)
    return question


def handle_new_question_request(bot, update):
    message_text = random.choice(list(quiz.keys()))
    update.message.reply_text(message_text)
    db_connection.set(update.message.from_user["id"], message_text)
    logger.info(f'правильный ответ: {quiz[message_text]}')
    return answer


def handle_solution_attempt(bot, update):
    user_answer = update.message.text
    correct_answer = fetch_correct_answer_by_user_id(update.message.from_user["id"], quiz, db_connection)
    if user_answer.strip().lower() == correct_answer:
        message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        update.message.reply_text(message_text)
        return question
    else:
        message_text = 'Неправильно… Попробуй ещё раз'
        update.message.reply_text(message_text)
        return answer


def handle_show_answer(bot, update):
    correct_answer = fetch_correct_answer_by_user_id(update.message.from_user["id"], quiz, db_connection)
    update.message.reply_text(f'Правильный ответ: {correct_answer}.\nДля следующего вопроса нажми "Новый вопрос"')
    return question


def cancel(bot, update):
    update.message.reply_text('Завершение работы викторины.', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error_handler(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    load_dotenv()
    quiz = get_quiz_questions_and_answers_from_file(os.environ['QUIZ_FILEPATH'])
    db_connection = redis.Redis(host=os.environ['REDIS_HOST'], port=os.environ['REDIS_PORT'], db=0,
                                password=os.environ['REDIS_PASSWORD'], decode_responses=True)
    question, answer = range(2)

    telegram_token = os.environ['TELEGRAM_TOKEN']
    telegram_chat_id = os.environ['TELEGRAM_CHAT_ID']

    logger_handler = TelegramBotHandler(telegram_token, telegram_chat_id)
    logger_handler.setLevel(logging.WARNING)
    logger_handler.formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    logger.addHandler(logger_handler)

    updater = Updater(telegram_token)
    updater.logger.addHandler(logger_handler)
    dispatcher = updater.dispatcher
    dispatcher.logger.addHandler(logger_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            question: [RegexHandler('^Новый вопрос$', handle_new_question_request),
                       CommandHandler('cancel', cancel)],

            answer: [RegexHandler('^Сдаться$', handle_show_answer),
                     MessageHandler(Filters.text, handle_solution_attempt),
                     CommandHandler('cancel', cancel)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()
