import logging
import os
import random

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler

from utils import (TelegramBotHandler, get_quiz_questions_and_answers_from_file, fetch_correct_answer_by_user_id,
                   establish_connection_redis_db)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

QUIZ = get_quiz_questions_and_answers_from_file(os.environ['QUIZ_FILEPATH'])

DB_CONNECTION = establish_connection_redis_db(os.environ['REDIS_HOST'],
                                              os.environ['REDIS_PORT'],
                                              os.environ['REDIS_PASSWORD'])

QUESTION, ANSWER = range(2)


def start(bot, update):
    """Send a message when the command /start is issued."""
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        'Привет! Я бот для викторин.\nНажмите "Новый вопрос" для начала викторины.\n/cancel - для отмены.',
        reply_markup=reply_markup)
    return QUESTION


def handle_new_question_request(bot, update):
    message_text = random.choice(list(QUIZ.keys()))
    update.message.reply_text(message_text)
    DB_CONNECTION.set(update.message.from_user["id"], message_text)
    logger.info(f'правильный ответ: {QUIZ[message_text]}')
    return ANSWER


def handle_solution_attempt(bot, update):
    answer = update.message.text
    correct_answer = fetch_correct_answer_by_user_id(update.message.from_user["id"], QUIZ, DB_CONNECTION)
    if answer.strip().lower() == correct_answer.lower():
        message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        update.message.reply_text(message_text)
        return QUESTION
    else:
        message_text = 'Неправильно… Попробуй ещё раз'
        update.message.reply_text(message_text)
        return ANSWER


def handle_show_answer(bot, update):
    correct_answer = fetch_correct_answer_by_user_id(update.message.from_user["id"], QUIZ, DB_CONNECTION)
    update.message.reply_text(f'Правильный ответ: {correct_answer}.\nДля следующего вопроса нажми "Новый вопрос"')
    return QUESTION


def cancel(bot, update):
    update.message.reply_text('Завершение работы викторины.', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error_handler(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
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
            QUESTION: [RegexHandler('^Новый вопрос$', handle_new_question_request),
                       CommandHandler('cancel', cancel)],

            ANSWER: [RegexHandler('^Сдаться$', handle_show_answer),
                     MessageHandler(Filters.text, handle_solution_attempt),
                     CommandHandler('cancel', cancel)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
