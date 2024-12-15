from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from groq import Client
import logging
from typing import Dict, List
import os
from datetime import datetime

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
    if update.message.chat_id != Config.OWNER_ID:
        user = update.message.from_user
        username = f"@{user.username}" if user.username else user.full_name
        context.bot.send_message(
            chat_id=Config.OWNER_ID,
            text=f"New user: {username}"
        )

def handle_message(update, context) -> None:
    """Handle incoming messages"""
    try:
        user_message = update.message.text.strip()
        user_id = update.message.from_user.id
        
        # Check for predefined responses
        if any(phrase in user_message.lower() for phrase in [
            "من هو ابراهيم سعدي",
            "how is ibrahim saadi"
        ]):
            update.message.reply_text(
                "ابراهيم سعدي طالب من جامعة نينوى و هو مبرمج البوت ومطور الذكاء الاصطناعي"
            )
            return

        # Get or create user session
        session = get_user_session(user_id)
        session.add_message("user", user_message)

        # Get AI response
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=session.context,
                model=Config.MODEL_NAME,
            )
            response = chat_completion.choices[0].message.content
            session.add_message("assistant", response)
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            response = "عذراً، حدث خطأ في معالجة طلبك. الرجاء المحاولة مرة أخرى لاحقاً."

        # Send response
        update.message.reply_text(response)
        
        # Notify owner
        if user_id != Config.OWNER_ID:
            user = update.message.from_user
            username = f"@{user.username}" if user.username else user.full_name
            context.bot.send_message(
                chat_id=Config.OWNER_ID,
                text=f"{username} -> {user_message}"
            )

    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}")
        update.message.reply_text("عذراً، حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى.")

def main() -> None:
    """Start the bot"""
    try:
        # Create the Updater and dispatcher
        updater = Updater(Config.TELEGRAM_BOT_TOKEN, use_context=True)
        dp = updater.dispatcher

        # Add handlers
        dp.add_handler(CommandHandler("start", start_command))
        dp.add_handler(CommandHandler("warning", warning_command))
        dp.add_handler(MessageHandler(
            Filters.text & ~Filters.command,
            handle_message
        ))

        # Start the bot
        logger.info("Starting bot...")
        updater.start_polling()
        updater.idle()

    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")

if __name__ == '__main__':
    main()
