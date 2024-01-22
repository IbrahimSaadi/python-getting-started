import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from bardapi import Bard

# Set your Bard API key
os.environ["_BARD_API_KEY"] = "fgiipqRVVvDXgwesAW08bCv_CT0Ii68qXGsU3alb1dka6aWBG4OzFqmKxLsVkDtZBbatgw."

# Define the function to handle incoming messages


def handle_message(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    response = Bard().get_answer(str(message_text))['content']
    update.message.reply_text(response)


def main():
    # Set your Telegram Bot token
    TELEGRAM_TOKEN = '5988601506:AAH_t0h3R7i7KBOHgbOHcVwnvyliKgf16c4'

    # Create the Updater and pass it your bot's token
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register the command handler for /start command

    # Register the message handler to handle all messages
    dp.add_handler(MessageHandler(Filters.text & ~
                   Filters.command, handle_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop it
    updater.idle()


if __name__ == '__main__':
    main()
