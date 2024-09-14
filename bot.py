import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from groq import Client

# Set up your Groq API client
GROQ_API_KEY = "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"
client = Client(api_key=GROQ_API_KEY)

# Telegram bot token from BotFather
TELEGRAM_BOT_TOKEN = "7389844135:AAFQNw2OA4zPyOUS3DtJ6Fb4c5CRpWSFHmw"

# Function to handle incoming messages


def AI_gemini(update, context):
    user_message = update.message.text

    # Make Groq API call
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="gemma2-9b-it",
        )
        response = chat_completion.choices[0].message.content
    except Exception as e:
        response = f"Error: {str(e)}"

    # Send the Groq API response back to the user
    update.message.reply_text(response)


def start(update, context):
    update.message.reply_text('انا ذكاء اصطناعي من كوكل، اسألني اي شيء!')


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Register handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~
                   Filters.command, AI_gemini))

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
