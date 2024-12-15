from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from groq import Client
import logging
from typing import Dict, List, Optional
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Load environment variables from .env file
load_dotenv()

# Configure logging with file output
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Config:
    """Configuration settings for the bot"""
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OWNER_ID = int(os.getenv("OWNER_ID", "1237470290"))
    MAX_CONTEXT_MESSAGES = 10
    MODEL_NAME = "gemma2-9b-it"
    INACTIVE_TIMEOUT = timedelta(minutes=30)
    MAX_RESPONSE_LENGTH = 4096  # Telegram's message length limit
    RATE_LIMIT = 20  # messages per minute
    BACKUP_FILE = "sessions_backup.json"

class UserSession:
    """Manages user conversation context and settings"""
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.context: List[Dict[str, str]] = []
        self.last_interaction: datetime = datetime.now()
        self.message_count: int = 0
        self.last_minute: datetime = datetime.now()
        self.language: str = "ar"  # Default language
        self.is_premium: bool = False
        
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation context"""
        self.context.append({"role": role, "content": content})
        if len(self.context) > Config.MAX_CONTEXT_MESSAGES:
            self.context.pop(0)
        self.last_interaction = datetime.now()
        
    def check_rate_limit(self) -> bool:
        """Check if user has exceeded rate limit"""
        now = datetime.now()
        if now - self.last_minute > timedelta(minutes=1):
            self.message_count = 0
            self.last_minute = now
        
        self.message_count += 1
        return self.message_count <= Config.RATE_LIMIT
    
    def to_dict(self) -> dict:
        """Convert session to dictionary for backup"""
        return {
            "user_id": self.user_id,
            "context": self.context,
            "language": self.language,
            "is_premium": self.is_premium
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserSession':
        """Create session from dictionary"""
        session = cls(data["user_id"])
        session.context = data["context"]
        session.language = data.get("language", "ar")
        session.is_premium = data.get("is_premium", False)
        return session

class BotManager:
    """Manages bot operations and state"""
    def __init__(self):
        self.groq_client = Client(api_key=Config.GROQ_API_KEY)
        self.sessions: Dict[int, UserSession] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.load_sessions()
        
    def get_user_session(self, user_id: int) -> UserSession:
        """Get or create user session"""
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession(user_id)
        return self.sessions[user_id]
    
    def save_sessions(self) -> None:
        """Backup sessions to file"""
        try:
            data = {str(uid): session.to_dict() for uid, session in self.sessions.items()}
            with open(Config.BACKUP_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Sessions backed up successfully")
        except Exception as e:
            logger.error(f"Error backing up sessions: {e}")
    
    def load_sessions(self) -> None:
        """Load sessions from backup file"""
        try:
            if os.path.exists(Config.BACKUP_FILE):
                with open(Config.BACKUP_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for uid, session_data in data.items():
                        self.sessions[int(uid)] = UserSession.from_dict(session_data)
                logger.info("Sessions loaded from backup")
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
    
    def cleanup_inactive_sessions(self) -> None:
        """Remove inactive sessions"""
        now = datetime.now()
        inactive_users = [
            uid for uid, session in self.sessions.items()
            if now - session.last_interaction > Config.INACTIVE_TIMEOUT
        ]
        for uid in inactive_users:
            del self.sessions[uid]
        if inactive_users:
            logger.info(f"Cleaned up {len(inactive_users)} inactive sessions")

    async def get_ai_response(self, session: UserSession, message: str) -> str:
        """Get AI response using Groq API"""
        try:
            chat_completion = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.groq_client.chat.completions.create(
                    messages=session.context,
                    model=Config.MODEL_NAME,
                    max_tokens=2048,
                    temperature=0.7,
                )
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return "عذراً، حدث خطأ في معالجة طلبك. الرجاء المحاولة مرة أخرى لاحقاً."

# Initialize bot manager
bot_manager = BotManager()

def build_language_keyboard() -> InlineKeyboardMarkup:
    """Create language selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data='lang_ar'),
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_help_message(language: str) -> str:
    """Get help message in specified language"""
    messages = {
        "ar": """📋 قائمة الأوامر المتاحة:
• /start - بدء المحادثة
• /help - عرض هذه المساعدة
• /lang - تغيير اللغة
• /clear - مسح سجل المحادثة
• /warning - عرض التحذيرات

للمساعدة التقنية، تواصل مع @ibrahimsaadi""",
        "en": """📋 Available Commands:
• /start - Start conversation
• /help - Show this help
• /lang - Change language
• /clear - Clear chat history
• /warning - Show warnings

For technical support, contact @ibrahimsaadi"""
    }
    return messages.get(language, messages["ar"])

async def start_command(update, context) -> None:
    """Handle /start command"""
    user_id = update.effective_user.id
    session = bot_manager.get_user_session(user_id)
    
    welcome_messages = {
        "ar": """مرحباً! 👋 
أنا مساعد ذكي يمكنني:
• الإجابة على أسئلتك
• المساعدة في المهام المختلفة
• التحدث بالعربية والإنجليزية
• توليد نصوص إبداعية

📝 للبدء، اختر لغتك المفضلة:""",
        "en": """Welcome! 👋
I'm an AI assistant that can:
• Answer your questions
• Help with various tasks
• Communicate in Arabic and English
• Generate creative text

📝 To begin, choose your preferred language:"""
    }
    
    message = welcome_messages.get(session.language, welcome_messages["ar"])
    await update.message.reply_text(message, reply_markup=build_language_keyboard())
    notify_owner(update, context)

async def help_command(update, context) -> None:
    """Handle /help command"""
    user_id = update.effective_user.id
    session = bot_manager.get_user_session(user_id)
    await update.message.reply_text(get_help_message(session.language))

async def lang_command(update, context) -> None:
    """Handle /lang command"""
    await update.message.reply_text(
        "Choose your language / اختر لغتك:",
        reply_markup=build_language_keyboard()
    )

async def clear_command(update, context) -> None:
    """Handle /clear command"""
    user_id = update.effective_user.id
    session = bot_manager.get_user_session(user_id)
    session.context = []
    messages = {
        "ar": "تم مسح سجل المحادثة ✨",
        "en": "Chat history cleared ✨"
    }
    await update.message.reply_text(messages.get(session.language, messages["ar"]))

async def language_callback(update, context) -> None:
    """Handle language selection callback"""
    query = update.callback_query
    user_id = query.from_user.id
    session = bot_manager.get_user_session(user_id)
    
    lang = query.data.split('_')[1]
    session.language = lang
    
    messages = {
        "ar": "تم تغيير اللغة إلى العربية 🇸🇦",
        "en": "Language changed to English 🇬🇧"
    }
    await query.answer()
    await query.edit_message_text(messages.get(lang, messages["ar"]))

async def handle_message(update, context) -> None:
    """Handle user messages"""
    try:
        user_id = update.effective_user.id
        session = bot_manager.get_user_session(user_id)
        
        # Check rate limit
        if not session.check_rate_limit():
            messages = {
                "ar": "عذراً، لقد تجاوزت الحد المسموح به من الرسائل. الرجاء المحاولة لاحقاً.",
                "en": "Sorry, you've exceeded the message limit. Please try again later."
            }
            await update.message.reply_text(messages.get(session.language, messages["ar"]))
            return
        
        user_message = update.message.text.strip()
        
        # Check predefined responses
        if any(phrase in user_message.lower() for phrase in [
            "من هو ابراهيم سعدي",
            "how is ibrahim saadi"
        ]):
            await update.message.reply_text(
                "ابراهيم سعدي طالب من جامعة نينوى و هو مبرمج البوت ومطور الذكاء الاصطناعي"
            )
            return
        
        session.add_message("user", user_message)
        
        # Get AI response
        response = await bot_manager.get_ai_response(session, user_message)
        
        # Split long responses
        if len(response) > Config.MAX_RESPONSE_LENGTH:
            parts = [response[i:i + Config.MAX_RESPONSE_LENGTH] 
                    for i in range(0, len(response), Config.MAX_RESPONSE_LENGTH)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(response)
        
        session.add_message("assistant", response)
        
        # Notify owner
        if user_id != Config.OWNER_ID:
            username = update.effective_user.username or update.effective_user.full_name
            await context.bot.send_message(
                chat_id=Config.OWNER_ID,
                text=f"{username} -> {user_message}"
            )
        
        # Periodic cleanup and backup
        if datetime.now().minute % 5 == 0:  # Every 5 minutes
            bot_manager.cleanup_inactive_sessions()
            bot_manager.save_sessions()
            
    except Exception as e:
        logger.error(f"Error in message handler: {e}")
        messages = {
            "ar": "عذراً، حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى.",
            "en": "Sorry, an unexpected error occurred. Please try again."
        }
        await update.message.reply_text(messages.get(session.language, messages["ar"]))

def notify_owner(update, context) -> None:
    """Notify bot owner of new users"""
    if update.message.chat_id != Config.OWNER_ID:
        user = update.message.from_user
        username = f"@{user.username}" if user.username else user.full_name
        context.bot.send_message(
            chat_id=Config.OWNER_ID,
            text=f"New user: {username}"
        )

def main() -> None:
    """Start the bot"""
    try:
        # Create the Updater and dispatcher
        updater = Updater(Config.TELEGRAM_BOT_TOKEN, use_context=True)
        dp = updater.dispatcher

        # Add handlers
        dp.add_handler(CommandHandler("start", start_command))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("lang", lang_command))
        dp.add_handler(CommandHandler("clear", clear_command))
        dp.add_handler(CommandHandler("warning", warning_command))
        dp.add_handler(CallbackQueryHandler(language_callback, pattern='^lang_'))
        dp.add_handler(MessageHandler(
            Filters.text & ~Filters.command,
            handle_message
        ))

        # Start the bot
        logger.info("Starting bot...")
        updater.start_polling()
        
        # Run the bot until you press Ctrl-C
        updater.idle()

    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == '__main__':
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(f'GROQ_API_KEY={Config.GROQ_API_KEY}\n')
