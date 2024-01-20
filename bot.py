from googletrans import Translator
import os
import shutil
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
import easyocr
from PIL import Image
import pytesseract
# your path may be different
#pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
# Replace 'YOUR_BOT_TOKEN' with the token you received from BotFather
BOT_TOKEN = '5988601506:AAH_t0h3R7i7KBOHgbOHcVwnvyliKgf16c4'
user_states = {}
# Create a directory to store user-specific data
DATA_DIR = 'user_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def startImage(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    context.user_data['state'] = 'idle'
    user_states[user_id] = context.user_data
    update.message.reply_text(
        "Send me an image, and I will translate the text in it to Arabic!")


def image_handler(update: Update, context: CallbackContext) -> None:
    global user_states
    user_id = update.message.chat_id
    context.user_data['state'] = 'idle'
    user_states[user_id] = context.user_data
    user_id = update.message.chat_id
    user_data = user_states.get(user_id, {})
    update.message.reply_text(
        "جاري استخراج النص للترجمة، يرجى الانتظار...")
    if user_data.get('state') == 'idle':
        # Create a directory for the user based on their chat ID
        user_dir = os.path.join(DATA_DIR, str(user_id))
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        # Initialize the EasyOCR reader
        # Get the image file
        file = update.message.photo[-1].get_file()
        image_path = os.path.join(user_dir, "image.jpg")
        file.download(image_path)
        # Perform OCR on the image
        results = Image.open(image_path)
        results = pytesseract.image_to_string(results)

        # Extract the recognized text
        # Initialize a translator object to perform translation
        translator = Translator()
        # Translate the extracted text to Arabic
        translated_text = translator.translate(results, dest='ar')
        # Save the translated text to a file
        translation_path = os.path.join(user_dir, "translation.txt")
        with open(translation_path, "w", encoding="utf-8") as f:
            f.write("Original Text:\n" + results +
                    "\n\nTranslated Text (Arabic):\n" + translated_text.text)
        # Send the translated text back to the user
        update.message.reply_text(
            "Original Text:\n" + results)
        update.message.reply_text(
            "\n\nTranslated Text (Arabic):\n" + translated_text.text)
        # Delete the user's directory
        shutil.rmtree(user_dir)
        user_data['state'] = 'idle'
        user_states[user_id] = user_data


def main() -> None:
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", startImage))
    dp.add_handler(MessageHandler(Filters.photo & ~
                   Filters.command, image_handler))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    user_states = {}  # Dictionary to store user states
    main()
