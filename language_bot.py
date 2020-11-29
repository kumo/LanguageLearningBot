#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to quiz vocabulary.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Simple bot to quiz vocabulary
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Use dotenv for bot token
import os
from os.path import join, dirname
from dotenv import load_dotenv

# Create .env file path.
dotenv_path = join(dirname(__file__), '.env')

# Load file from the path.
load_dotenv(dotenv_path)

# Get variables from the environment
BOT_TOKEN = os.getenv('BOT_TOKEN')

import datetime
import random

QUESTIONS = [
    ['おはよう', 'Good morning'],
    ['おはようございます', 'Good morning (polite)'],
    ['おやすみ（なさい）', 'Good night'],
    ['ごちそうさま（でした）', 'Thank you for the meal (after eating)'],
    ['よろしくおねがいします', 'Nice to meet you'],
    ['はじめまして', 'How do you do?'],
    ['すみません', "Excuse me;I'm sorry"],
    ['ただいま', "I'm home"],
    ['さようなら', 'Good bye'],
    ['こんばんは', 'Good evening'],
    ['こんにちは', 'Good afternoon'],
    ['おかえり（なさい）', 'Welcome home'],
    ['いってらっしゃい', 'Please go and come back'],
    ['いってきます', 'I’ll go and come back'],
    ['いいえ', 'No;Not at all'],
    ['ありがとうございます', 'Thank you (polite)'],
    ['ありがとう', 'Thank you'],
]

def send_greeting(update: Update, context: CallbackContext) -> None:
    now = datetime.datetime.now()

    if now.hour < 11:
        update.message.reply_text("おはよう")
    elif now.hour < 19:
        update.message.reply_text("こんにちは")
    else:
        update.message.reply_text("こんばんは")


def choose_questions(num_questions):
    random.shuffle(QUESTIONS)

    questions = QUESTIONS[:num_questions]

    return questions


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""

    send_greeting(update, context)

    start_quiz(update, context)


def start_quiz(update: Update, context: CallbackContext) -> None:
    questions = choose_questions(5)

    context.user_data['questions'] = questions
    context.user_data['question_num'] = 0
    context.user_data['correct'] = 0

    update.message.reply_text("I will now ask you {} questions.".format(5))

    ask_question(update, context)


def ask_question(update: Update, context: CallbackContext) -> None:
    questions = context.user_data['questions']
    question_num = context.user_data['question_num']

    question = questions[question_num]
    update.message.reply_text(question[0])


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def check_answer(question, reply) -> bool:
    if ';' in question[1]:
        answers = question[1].split(';')

        for answer in answers:
            if reply == answer:
                return True
        
        return False

    else:
        if reply == question[1]:
            return True
        else:
            return False


def check_response(update: Update, context: CallbackContext) -> None:
    """Check the user's response."""

    question_num = context.user_data['question_num']
    questions = context.user_data['questions']

    question = questions[question_num]

    result = check_answer(question, update.message.text)

    if result == True:
        update.message.reply_text('Correct!')
        context.user_data['correct'] += 1
    else:
        update.message.reply_text('The correct answer was "{}".'.format(question[1]))

    question_num = question_num + 1
    context.user_data['question_num'] = question_num

    if question_num == 5:
        end_quiz(update, context)
    else:
        ask_question(update, context)


def end_quiz(update: Update, context: CallbackContext) -> None:
    correct = context.user_data['correct']
    
    update.message.reply_text('You scored {} out of {}.'.format(correct, 5))
    update.message.reply_text('To try again, just /start.')


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, check_response))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
