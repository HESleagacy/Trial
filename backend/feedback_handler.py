# backend/feedback_handler.py
# Purpose: Load and use AventIQ-AI sentiment model for patient reviews

from transformers import BertForSequenceClassification, BertTokenizer
import torch

# Model and tokenizer from Hugging Face
MODEL_NAME = "AventIQ-AI/sentiment-analysis-for-patient-reviews-analysis"
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertForSequenceClassification.from_pretrained(MODEL_NAME)

# Set to eval mode + FP16 for speed
model.eval()
model.half()

# Label mapping from model
LABEL_MAP = {
    0: "very_negative",
    1: "negative",
    2: "neutral",
    3: "positive",
    4: "very_positive"
}

def analyze_sentiment(feedback: str) -> str:
    """
    Analyze patient feedback using quantized BERT model.
    Returns: one of 5 sentiment labels
    """
    # Tokenize input
    inputs = tokenizer(
        feedback,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128
    )
    
    # Convert to correct types
    inputs = {k: v.long() for k, v in inputs.items()}
    
    # Predict
    with torch.no_grad():
        outputs = model(**inputs)
        predicted_class = torch.argmax(outputs.logits, dim=1).item()
    
    return LABEL_MAP[predicted_class]
