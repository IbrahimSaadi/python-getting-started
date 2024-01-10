from PIL import Image
import pytesseract
# your path may be different
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = '/app/.apt/usr/bin//Tesseract-OCR/tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = '/app/.apt/usr/bin/tesseract'


def extract_text_from_image(image_path):
    try:
        # Open the image file
        img = Image.open(image_path)

        # Use pytesseract to do OCR on the image
        text = pytesseract.image_to_string(img)

        return text
    except Exception as e:
        return str(e)


if __name__ == "__main__":
    # Replace 'your_image_path.jpg' with the path to your image file
    image_path = 'image.jpg'

    result = extract_text_from_image(image_path)

    print("OCR Result:")
    print(result)
