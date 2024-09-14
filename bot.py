from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from groq import Client
# Set up your Groq API client
GROQ_API_KEY = "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"
client = Client(api_key=GROQ_API_KEY)
# Telegram bot token from BotFather
TELEGRAM_BOT_TOKEN = "7389844135:AAFQNw2OA4zPyOUS3DtJ6Fb4c5CRpWSFHmw"
myID = 1237470290
# Function to handle incoming messages


def AI_gemini(update, context):
    user_message = update.message.text
    chat_id = update.message.chat_id

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
    if chat_id != myID:
        if update.message.from_user.username is not None:
            context.bot.send_message(chat_id=myID,
                                     text='@' + update.message.from_user.username +
                                     '->' + user_message)
        else:
            context.bot.send_message(chat_id=myID,
                                     text=update.message.from_user.full_name +
                                     '->' + user_message)


def warning(update, context):
    update.message.reply_text("""⚠️يُرجى ملاحظة أن  ذكاء اصطناعي قد لايمتلك معارفٌ حقيقية أو فهمٍ عميقٍ للعالم. ⚠️
⚠️الأجوبة التي ينتجها قد تكون دقيقة أحيانًا، لكن لا يمكن الاعتماد عليها كمعلوماتٍ موثوقةٍ. ⚠️""")


def start(update, context):
    update.message.reply_text("""أنا مساعد افتراضي ذكي بواسطة Gemini من  Google،  أستطيع فهمك وتقديم إجابات على الأسئلة، والكلام معك  وتوليد نصوص جديدة ومساعدة الطلاب. 🤖
أنا أتعلم من كميات كبيرة من النصوص، لذا أصبحت ماهرًا في العديد من المهام مثل الترجمة، والكتابة الإبداعية،  وإنشاء ملخصات. 🧠
!!!!!!هي اسالني!!!!!!
تحذير
/warning""")
    chat_id = update.message.chat_id
    if chat_id != myID:
        if update.message.from_user.username is not None:
            context.bot.send_message(chat_id=myID,
                                     text='@' + update.message.from_user.username)
        else:
            context.bot.send_message(chat_id=myID,
                                     text=update.message.from_user.full_name)


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    # Register handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("warning", warning))
    dp.add_handler(MessageHandler(Filters.text & ~
                   Filters.command, AI_gemini))
    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
