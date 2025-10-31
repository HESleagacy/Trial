# backend/ocr_processor.py
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
from .drug_matcher import match_drug  # ← Import here


def extract_from_image(file_content: bytes, content_type: str):
    # --- Open image ---
    if content_type == "application/pdf":
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(file_content, dpi=300)
        image = images[0]
    else:  # PNG / JPEG
        image = Image.open(io.BytesIO(file_content))

    # --- Pre-process (makes ANY image work) ---
    image = image.convert("L")  # grayscale
    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = image.filter(ImageFilter.SHARPEN)
    if image.width < 800:  # upscale tiny images
        scale = max(2, 800 // image.width)
        image = image.resize(
            (image.width * scale, image.height * scale),
            Image.LANCZOS
        )

    # --- OCR ---
    raw_text = pytesseract.image_to_string(image, lang="eng")

    # --- Use drug_matcher (centralized, fast, no duplicate logic) ---
    match = match_drug(raw_text, min_score=70)  # ← CALL IT HERE

    return {
        "name": match["name"] if match else "",
        "dose": match["dose"] if match else "",
        "raw_text": raw_text[:200]  # optional debug
    }
