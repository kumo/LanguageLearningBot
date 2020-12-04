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

from telegram import Update, ReplyKeyboardMarkup
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
import string

NUM_QUESTIONS = 5
questions = []

def send_greeting(update: Update, context: CallbackContext) -> None:
    now = datetime.datetime.now()

    if now.hour < 11:
        update.message.reply_text("おはよう")
    elif now.hour < 19:
        update.message.reply_text("こんにちは")
    else:
        update.message.reply_text("こんばんは")


def choose_questions(question_set, num_questions):
    random.shuffle(question_set)

    questions = question_set[:num_questions]

    for i, question in enumerate(questions):
        question_type = random.choice(['japanese', 'english'])

        question['question_type'] = question_type

        if ';' in question[question_type]:
            possible_questions = question[question_type].split(';')

            question_text = random.choice(possible_questions)
            question['question_text'] = question_text
        else:
            question['question_text'] = question[question_type]

        if question_type == 'japanese':
            question['answer_text'] = question['english']
        else:
            question['answer_text'] = question['japanese']

    return questions


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    global questions

    send_greeting(update, context)

    question_sets = [*questions.keys()]

    if len(question_sets) == 1:
        start_quiz(question_sets[0], update, context)
    else:
        # Show the user the list of available question sets
        quiz_keyboard = [[question_set] for question_set in question_sets]

        quiz_markup = ReplyKeyboardMarkup(quiz_keyboard, one_time_keyboard=True)

        update.message.reply_text("Choose the questions that you want to be tested on.", reply_markup=quiz_markup)


def start_quiz(quiz_name: str, update: Update, context: CallbackContext) -> None:
    global questions
    
    question_set = questions[quiz_name]

    chosen_questions = choose_questions(question_set, NUM_QUESTIONS)

    context.user_data['quiz_name'] = quiz_name
    context.user_data['questions'] = chosen_questions
    context.user_data['question_num'] = 0
    context.user_data['correct'] = 0

    update.message.reply_text("I will now ask you {} questions.".format(len(chosen_questions)))

    ask_question(update, context)


def ask_question(update: Update, context: CallbackContext) -> None:
    questions = context.user_data['questions']
    question_num = context.user_data['question_num']

    question = questions[question_num]

    update.message.reply_text(question['question_text'])


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def compare_text(text1, text2) -> bool:
    cleaned_text1 = text1.translate(str.maketrans('', '', string.punctuation))
    cleaned_text2 = text2.translate(str.maketrans('', '', string.punctuation))

    return cleaned_text1.casefold() == cleaned_text2.casefold()


def check_answer(correct_answer, response) -> bool:
    if ';' in correct_answer:
        correct_answers = correct_answer.split(';')

        for alternative_answer in correct_answers:
            if compare_text(alternative_answer, response):
                return True
        
        return False

    else:
        if compare_text(correct_answer, response):
            return True
        else:
            return False


def check_response(update: Update, context: CallbackContext) -> None:
    """Check the user's response."""

    if 'quiz_name' not in context.user_data:
        start_quiz(update.message.text, update, context)
        return

    question_num = context.user_data['question_num']
    questions = context.user_data['questions']

    question = questions[question_num]
    answer_text = question['answer_text']

    result = check_answer(answer_text, update.message.text)

    if result == True:
        update.message.reply_text('Correct!')
        context.user_data['correct'] += 1

        # TODO tell the alternative answer(s) to the user
        if ';' in answer_text:
            update.message.reply_text('Do not forget that there are alternative answers!')

    else:
        # TODO format the text properly if there are multiple correct answers
        update.message.reply_text('The correct answer was "{}".'.format(answer_text))

    question_num = question_num + 1
    context.user_data['question_num'] = question_num

    if question_num == len(questions):
        end_quiz(update, context)
    else:
        ask_question(update, context)


def end_quiz(update: Update, context: CallbackContext) -> None:
    correct = context.user_data['correct']
    questions = context.user_data['questions']

    update.message.reply_text('You scored {} out of {}.'.format(correct, len(questions)))
    update.message.reply_text('To try again, just /start.')

    if 'quiz_name' in context.user_data:
        del context.user_data['quiz_name']


import toml

def load_questions():
    global questions
    
    questions = toml.load("genki1.toml")

    print(questions)


def main():
    load_questions()

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
