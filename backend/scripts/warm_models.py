"""Download pinned embedding weights and verify the pretrained spaCy pipeline."""

from app.ml.embeddings import embed_sections, model_version
from app.nlp.parser import ner_model

if __name__ == "__main__":
    ner_model()
    result = embed_sections({"skills": "Python FastAPI PostgreSQL"})
    print(f"Loaded {model_version()}; embedding dimension = {len(result[0][2])}")
