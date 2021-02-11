import logging
import os
import random

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler

import main
from redis_db import db_connection
from utils import TelegramBotHandler

logger = logging.getLogger(__name__)
QUIZ = main.main()
QUESTION, ANSWER = range(2)


def start(bot, update):
    """Send a message when the command /start is issued."""
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        'Привет! Я бот для викторин.\nНажмите "Новый вопрос" для начала викторины.\n/cancel - для отмены.',
        reply_markup=reply_markup)
    return QUESTION


def help_command(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Помощь')


def repeat_text(bot, update):
    """Echo the user message."""
    if update.message.text == 'Новый вопрос':
        message_text = random.choice(list(QUIZ.keys()))
        update.message.reply_text(message_text)
        db_connection.set(update.message.from_user["id"], message_text)
    else:
        answer = update.message.text
        question = db_connection.get(update.message.from_user["id"])
        correct_answer = QUIZ[question].lower().strip()
        correct_answer = correct_answer.split('.')[0]
        correct_answer = correct_answer.split('(')[0].strip()
        print(f'правильный ответ: {correct_answer}')
        if answer.strip().lower() == correct_answer:
            message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        else:
            message_text = 'Неправильно… Попробуешь ещё раз?'
        update.message.reply_text(message_text)


def handle_new_question_request(bot, update):
    message_text = random.choice(list(QUIZ.keys()))
    update.message.reply_text(message_text)
    db_connection.set(update.message.from_user["id"], message_text)
    correct_answer = QUIZ[message_text].lower().strip()
    correct_answer = correct_answer.split('.')[0]
    correct_answer = correct_answer.split('(')[0].strip()
    print(f'правильный ответ: {correct_answer}')
    return ANSWER


def handle_solution_attempt(bot, update):
    answer = update.message.text
    question = db_connection.get(update.message.from_user["id"])
    correct_answer = QUIZ[question].lower().strip()
    correct_answer = correct_answer.split('.')[0]
    correct_answer = correct_answer.split('(')[0].strip()
    print(f'правильный ответ: {correct_answer}')
    if answer.strip().lower() == correct_answer:
        message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        update.message.reply_text(message_text)
        return QUESTION
    else:
        message_text = 'Неправильно… Попробуешь ещё раз?'
        update.message.reply_text(message_text)
        return ANSWER


def handle_show_answer(bot, update):
    question = db_connection.get(update.message.from_user["id"])
    correct_answer = QUIZ[question].lower().strip()
    correct_answer = correct_answer.split('.')[0]
    correct_answer = correct_answer.split('(')[0].strip()
    print(f'правильный ответ: {correct_answer}')
    update.message.reply_text(f'правильный ответ: {correct_answer}')
    return QUESTION


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error_handler(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    load_dotenv()
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
    # dispatcher.add_handler(CommandHandler('start', start))
    # dispatcher.add_handler(CommandHandler('help', help_command))
    # dispatcher.add_handler(MessageHandler(Filters.text, repeat_text))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            QUESTION: [RegexHandler('^Новый вопрос$', handle_new_question_request),
                       CommandHandler('cancel', cancel)],

            ANSWER: [RegexHandler('^Сдаться$', handle_show_answer),
                     MessageHandler(Filters.text, handle_solution_attempt),
                     CommandHandler('cancel', cancel)]

            # PHOTO: [MessageHandler(Filters.photo, photo),
            #         CommandHandler('skip', skip_photo)],
            #
            # LOCATION: [MessageHandler(Filters.location, location),
            #            CommandHandler('skip', skip_location)],
            #
            # BIO: [MessageHandler(Filters.text, bio)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
