from functools import lru_cache

import numpy as np

from app.core.config import settings


@lru_cache
def encoder():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        settings().embedding_model,
        revision=settings().embedding_revision,
        device="cpu",
        trust_remote_code=False,
    )
    if model.get_sentence_embedding_dimension() != 384:
        raise ValueError(
            "Configured model must produce 384 dimensions; migrate vectors before changing dimensions"
        )
    return model


def model_version():
    return f"{settings().embedding_model}@{settings().embedding_revision}"


def embed_sections(sections: dict[str, str]):
    model = encoder()
    chunks = []
    for section, text in sections.items():
        tokens = model.tokenizer.encode(text, add_special_tokens=False)
        size = min(model.max_seq_length - 2, 240)
        for offset in range(0, len(tokens), size - 32):
            chunk = model.tokenizer.decode(tokens[offset : offset + size], skip_special_tokens=True)
            chunks.append((section, chunk))
    if not chunks:
        raise ValueError("NO_QUALIFICATION_SECTIONS")
    vectors = model.encode(
        [text for _, text in chunks], batch_size=16, normalize_embeddings=True, show_progress_bar=False
    )
    return [(section, text, vector.tolist()) for (section, text), vector in zip(chunks, vectors, strict=True)]


def semantic_score(resume_vectors, job_vectors):
    if not resume_vectors or not job_vectors:
        raise ValueError("MISSING_EMBEDDINGS")
    similarities = np.asarray(job_vectors) @ np.asarray(resume_vectors).T
    # Each job chunk receives its strongest qualification evidence; mean over job chunks.
    return float(np.clip(similarities.max(axis=1), 0, 1).mean() * 100)
