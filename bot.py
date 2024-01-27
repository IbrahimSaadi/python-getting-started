from pytesseract import image_to_string
from PIL import Image
import pytesseract
# your path may be different
#pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'


print(pytesseract.image_to_string(
    'image.png', lang='ara'))
