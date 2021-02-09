import logging
import os
import random
import main
import redis

import telegram
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from utils import TelegramBotHandler

logger = logging.getLogger(__name__)
QUIZ = main.main()


def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Привет! Я бот для викторин')


def help_command(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Помощь')


def repeat_text(bot, update):
    """Echo the user message."""
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    if update.message.text == 'Новый вопрос':
        message_text = random.choice(list(QUIZ.keys()))
        update.message.reply_text(message_text, reply_markup=reply_markup)


def error_handler(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    load_dotenv()
    telegram_token = os.environ['TELEGRAM_TOKEN']
    telegram_chat_id = os.environ['TELEGRAM_CHAT_ID']
    radis_host = os.environ['RADIS_HOST']
    radis_port = os.environ['RADIS_PORT']
    database_connect = redis.Redis(host=radis_host, port=radis_port, db=0)

    logger_handler = TelegramBotHandler(telegram_token, telegram_chat_id)
    logger_handler.setLevel(logging.WARNING)
    logger_handler.formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    logger.addHandler(logger_handler)

    updater = Updater(telegram_token)
    updater.logger.addHandler(logger_handler)
    dispatcher = updater.dispatcher
    dispatcher.logger.addHandler(logger_handler)
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(MessageHandler(Filters.text, repeat_text))
    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
