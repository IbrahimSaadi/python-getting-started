from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from groq import Client
from dotenv import load_dotenv
import logging
from typing import Dict, List
import os
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_telegram_token")
    OWNER_ID = int(os.getenv("OWNER_ID", "1237470290"))
    MAX_CONTEXT_MESSAGES = 5
    MODEL_NAME = "gemma2-9b-it"

# Initialize clients
groq_client = Client(api_key=Config.GROQ_API_KEY)

# User session management
class UserSession:
    def __init__(self):
        self.context: List[Dict[str, str]] = []
        self.last_interaction: datetime = datetime.now()

    def add_message(self, role: str, content: str) -> None:
        self.context.append({"role": role, "content": content})
        if len(self.context) > Config.MAX_CONTEXT_MESSAGES:
            self.context.pop(0)
        self.last_interaction = datetime.now()

    def clear_messages(self) -> None:
        self.context = []
        self.last_interaction = datetime.now()

# Global session store
sessions: Dict[int, UserSession] = {}

def get_user_session(user_id: int) -> UserSession:
    if user_id not in sessions:
        sessions[user_id] = UserSession()
    return sessions[user_id]

# Command handlers
def start_command(update, context) -> None:
    """Handle the /start command"""
    welcome_message = """مرحباً! 👋 
أنا مساعد افتراضي ذكي بواسطة Gemini من Google.
🤖 يمكنني:
• فهم أسئلتك والإجابة عليها
• المساعدة في المهام المختلفة
• التحدث باللغتين العربية والإنجليزية
• توليد نصوص إبداعية

📝 للبدء، ما رأيك أن تسألني سؤالاً؟
⚠️ للتحذيرات المهمة: /warning"""

    update.message.reply_text(welcome_message)
    notify_owner(update, context)

def warning_command(update, context) -> None:
    """Handle the /warning command"""
    warning_message = """⚠️ تحذيرات مهمة:

• هذا المساعد يعتمد على الذكاء الاصطناعي ولا يمتلك فهماً حقيقياً للعالم
• الإجابات قد تكون دقيقة أحياناً لكنها ليست موثوقة دائماً
• يُرجى التحقق من المعلومات المهمة من مصادر موثوقة
• لا تشارك معلومات شخصية أو حساسة

شكراً لتفهمك! 🙏"""
    
    update.message.reply_text(warning_message)

def notify_owner(update, context) -> None:
    """Notify the bot owner of new users"""
    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.full_name
    context.bot.send_message(
        chat_id=Config.OWNER_ID,
        text=f"New user: {username} has started the bot."
    )

def ask_answer_type(update, context) -> None:
    """Ask the user if they need a short or detailed answer"""
    keyboard = [
        [InlineKeyboardButton("إجابة قصيرة", callback_data="short_answer"),
         InlineKeyboardButton("إجابة مفصلة", callback_data="detailed_answer")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("هل ترغب بإجابة قصيرة أم مفصلة؟", reply_markup=reply_markup)

def handle_message(update, context) -> None:
    """Handle incoming messages"""
    try:
        user_message = update.message.text.strip()
        user_id = update.message.from_user.id

        # Notify owner about the user's message
        user = update.message.from_user
        username = f"@{user.username}" if user.username else user.full_name
        context.bot.send_message(
            chat_id=Config.OWNER_ID,
            text=f"{username} sent a message: {user_message}"
        )

        # Check for predefined responses
        if any(phrase in user_message.lower() for phrase in [
            "من هو ابراهيم سعدي",
            "how is ibrahim saadi"
        ]):
            update.message.reply_text(
                "ابراهيم سعدي طالب من جامعة نينوى و هو مبرمج البوت ومطور الذكاء الاصطناعي"
            )
            return

        # Save the user message in the session
        session = get_user_session(user_id)
        session.add_message("user", user_message)

        # Ask for answer type
        ask_answer_type(update, context)

    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}")
        update.message.reply_text("عذراً، حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى.")

def handle_answer_type(update, context) -> None:
    """Handle the user's choice of answer type"""
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    session = get_user_session(user_id)

    try:
        answer_type = query.data
        messages = session.context

        if answer_type == "short_answer":
            # Fetch a concise response
            response = groq_client.chat.completions.create(
                messages=messages,
                model=Config.MODEL_NAME,
                max_tokens=50  # Limit response length
            ).choices[0].message.content
        else:
            # Fetch a detailed response
            response = groq_client.chat.completions.create(
                messages=messages,
                model=Config.MODEL_NAME
            ).choices[0].message.content

        # Save the assistant's response
        session.add_message("assistant", response)

        # Send the response
        query.edit_message_text(response)

    except Exception as e:
        logger.error(f"Groq API error: {str(e)}")
        query.edit_message_text("عذراً، حدث خطأ في معالجة طلبك. الرجاء المحاولة مرة أخرى لاحقاً.")

def clear_messages_command(update, context) -> None:
    """Clear the user's session messages"""
    user_id = update.message.from_user.id
    session = get_user_session(user_id)
    session.clear_messages()
    update.message.reply_text("تم مسح سجل الرسائل الخاص بك بنجاح! 😊")

    # Notify the owner about the cleared messages
    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.full_name
    context.bot.send_message(
        chat_id=Config.OWNER_ID,
        text=f"{username} has cleared their message history."
    )

def main() -> None:
    """Start the bot"""
    try:
        # Create the Updater and dispatcher
        updater = Updater(Config.TELEGRAM_BOT_TOKEN, use_context=True)
        dp = updater.dispatcher

        # Add handlers
        dp.add_handler(CommandHandler("start", start_command))
        dp.add_handler(CommandHandler("warning", warning_command))
        dp.add_handler(CommandHandler("clear", clear_messages_command))
        dp.add_handler(MessageHandler(
            Filters.text & ~Filters.command,
            handle_message
        ))
        dp.add_handler(CallbackQueryHandler(handle_answer_type))

        # Start the bot
        logger.info("Starting bot...")
        updater.start_polling()
        updater.idle()

    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")

if __name__ == '__main__':
    main()
