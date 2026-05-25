import re
import string

# Common filler words in spoken healthcare input
FILLER_WORDS = {
    "i", "have", "am", "feeling", "a", "an", "the",
    "is", "are", "was", "were", "my", "me"
}

def preprocess_text(text: str) -> str:
    """
    Preprocess text specifically for medical symptom normalization.
    Designed for embedding + FAISS similarity matching.
    """

    if not text or not isinstance(text, str):
        return ""

    # 1. Lowercase (important for consistent embeddings)
    text = text.lower()

    # 2. Remove punctuation but keep medical hyphen words
    text = text.translate(str.maketrans('', '', string.punctuation.replace("-", "")))

    # 3. Remove numbers only if standalone (keep things like 'covid-19')
    text = re.sub(r'\b\d+\b', '', text)

    # 4. Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # 5. Remove common filler words (spoken voice cleanup)
    tokens = text.split()
    tokens = [word for word in tokens if word not in FILLER_WORDS]

    cleaned_text = " ".join(tokens)

    return cleaned_text