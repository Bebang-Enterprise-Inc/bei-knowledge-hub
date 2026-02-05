"""Embedding generation (placeholder for actual implementation)."""

from typing import List


def generate_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
    """
    Generate embedding vector for text.

    Args:
        text: Text to embed
        task_type: "RETRIEVAL_QUERY" or "RETRIEVAL_DOCUMENT"

    Returns:
        768-dimensional embedding vector
    """
    # TODO: Implement with actual embedding model (e.g., sentence-transformers)
    # For now, return dummy vector
    return [0.0] * 768
