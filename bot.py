from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

# Replace 'YOUR_BOT_TOKEN' with the actual token you obtained from BotFather
TOKEN = 'YOUR_BOT_TOKEN'

def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Hello! I'm your bot.")

def echo(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=update.message.text)

def main():
    # Create the Updater and pass it your bot's token
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))

    # Register a message handler for text messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop it
    updater.idle()

if __name__ == '__main__':
    main()
