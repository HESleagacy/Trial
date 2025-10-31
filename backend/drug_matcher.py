# backend/drug_matcher.py
# ----------------------------------------------------------------------
# Purpose:  Fuzzy-match OCR-extracted text against the canonical drug list
#           (backend/data/drug_list.json).  Returns the best-matching
#           {name, dose} entry with a confidence score.
#
# Why a separate file?
#   • Keeps OCR logic clean (ocr_processor.py only does image → text)
#   • Re-usable for manual entry validation (optional later)
#   • Easy to swap matching algorithm (Levenshtein, embeddings, etc.)
# ----------------------------------------------------------------------

import json
from typing import Optional, Dict
from fuzzywuzzy import fuzz

# ----------------------------------------------------------------------
# Load the reference drug list once at import time (fast, no I/O per request)
# ----------------------------------------------------------------------
with open("backend/data/drug_list.json", "r", encoding="utf-8") as f:
    DRUG_REFERENCE: list[Dict[str, str]] = json.load(f)   # [{"name": "...", "dose": "..."}, ...]

# ----------------------------------------------------------------------
# Core matching function
# ----------------------------------------------------------------------
def match_drug(ocr_text: str, min_score: int = 75) -> Optional[Dict[str, any]]:
    """
    Find the best-matching drug from OCR text.

    Args:
        ocr_text (str): Raw text returned by Tesseract.
        min_score (int): Minimum fuzzy partial-ratio to accept a match (0-100).

    Returns:
        dict | None:
            {
                "name": str,
                "dose": str,
                "confidence": float   # 0.0 – 1.0
            }
            or None if no match meets the threshold.
    """
    if not ocr_text.strip():
        return None

    ocr_lower = ocr_text.lower()
    best_match: Optional[Dict[str, any]] = None
    best_score: int = 0

    # ------------------------------------------------------------------
    # 1. Try exact name match first (fast path)
    # 2. Fall back to fuzzy partial ratio on the whole line
    # ------------------------------------------------------------------
    for drug in DRUG_REFERENCE:
        drug_name = drug["name"].lower()

        # Exact name match (e.g., "metformin" appears anywhere)
        if drug_name in ocr_lower:
            score = 100
        else:
            # Fuzzy partial ratio – tolerant to surrounding text
            score = fuzz.partial_ratio(ocr_lower, drug_name)

        if score > best_score and score >= min_score:
            best_score = score
            best_match = {
                "name": drug["name"],
                "dose": drug["dose"],
                "confidence": round(score / 100.0, 2)
            }

    return best_match
