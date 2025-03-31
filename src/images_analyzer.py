from PIL import Image
import pytesseract
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration

# --- OCR Function ---
def extract_ocr_text(image_path, thresholding=True):
    """Extracts text using pytesseract with optional preprocessing.
    Will only work with either English or French text.
    Args:
        image_path (str): Path to the image file.
        thresholding (bool): Whether to apply thresholding to the image.
        Returns:
        str: Extracted text from the image.
        """
    
    image = Image.open(image_path).convert("RGB")
    if thresholding:
        gray = image.convert("L")
        image = gray.point(lambda x: 0 if x < 160 else 255)
    return pytesseract.image_to_string(image, lang="eng+fra").strip()

# --- BLIP Function ---
def generate_blip_caption(image_path):
    """Generates image description using BLIP model. 
    Will be used as a fallback if OCR fails to extract text.
        Args:
        image_path (str): Path to the image file.
        Returns:
        str: Generated caption for the image.
        """
    image = Image.open(image_path).convert("RGB")
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    inputs = processor(image, return_tensors="pt")
    out = model.generate(**inputs)
    return processor.decode(out[0], skip_special_tokens=True)

# --- Smart Fallback Wrapper ---
def generate_alt_text(image_path, ocr_threshold=10):
    """Smart alt-text generator using OCR + fallback to BLIP.
    Will first try to extract text using OCR, and if the text is below a certain threshold,
    it will fallback to BLIP for image description.
    Args:
        image_path (str): Path to the image file.
        ocr_threshold (int): Minimum length of OCR text to consider it valid.
        Returns:
        str: Alt text for the image.
        """
    text = extract_ocr_text(image_path)
    if len(text) >= ocr_threshold:
        return f"Text in image: {text}"
    try:
        caption = generate_blip_caption(image_path)
        return f"Image description: {caption}"
    except Exception:
        return "Image description unavailable (BLIP failed)."
    
print("OCR:", extract_ocr_text("../data/your_image.jpg"))
print("Caption:", generate_blip_caption("../data/your_image.jpg"))

alt = generate_alt_text("../data/your_image.jpg")
print(alt)