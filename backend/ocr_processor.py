# backend/ocr_processor.py
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import json
from fuzzywuzzy import fuzz

with open("backend/data/drug_list.json", "r", encoding="utf8") as f:
    DRUG_LIST = json.load(f)

def extract_from_image(file_content: bytes, content_type: str):
    # --- open image ---
    if content_type == "application/pdf":
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(file_content, dpi=300)
        image = images[0]
    else:   # PNG / JPEG
        image = Image.open(io.BytesIO(file_content))

    # --- PRE‑PROCESS (makes ANY PNG work) ---
    image = image.convert("L")                     # grayscale
    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = image.filter(ImageFilter.SHARPEN)
    if image.width < 800:                          # upscale tiny images
        scale = max(2, 800 // image.width)
        image = image.resize((image.width*scale, image.height*scale), Image.LANCZOS)

    # --- OCR ---
    raw_text = pytesseract.image_to_string(image, lang="eng")
    text_lower = raw_text.lower()

    # --- FIRST MATCH ONLY (your requirement) ---
    for drug in DRUG_LIST:
        full = f"{drug['name'].lower()} {drug['dose'].lower()}"
        if full in text_lower:
            return {"name": drug["name"], "dose": drug["dose"], "raw_text": raw_text[:300]}
        if fuzz.partial_ratio(text_lower, drug["name"].lower()) > 80:
            return {"name": drug["name"], "dose": drug["dose"], "raw_text": raw_text[:300]}

    return {"name": "", "dose": "", "raw_text": raw_text[:300]}
