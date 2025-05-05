# images_analyzer.py

import pytesseract
from PIL import Image

def generate_alt_text(image_path):
    """
    Génère un alt-text simple via OCR.
    Pour un usage pro, remplacer par BLIP ou un modèle visuel+langage.
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img).strip()
        if text:
            return text
    except Exception:
        pass
    # fallback
    return "Image"


if __name__ == "__main__":
    import sys
    print(generate_alt_text(sys.argv[1]))
