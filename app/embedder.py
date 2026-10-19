from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-small"
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def embed_passages(texts: list[str]) -> list[list[float]]:
    vectors = get_model().encode(
        [f"passage: {t}" for t in texts],
        normalize_embeddings=True,
        batch_size=32
    )
    return vectors.tolist()

def embed_query(text: str) -> list[float]:
    vector = get_model().encode(f"query: {text}", normalize_embeddings=True)
    return vector.tolist()