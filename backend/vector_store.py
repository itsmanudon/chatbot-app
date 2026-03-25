"""
vector_store.py
---------------
Pinecone vector database integration for semantic memory retrieval.

The ``VectorStore`` class wraps the Pinecone client and provides three
operations used by the memory engine:

1. **Generate embeddings** — converts raw text into a 384-dimensional
   floating-point vector using the ``llama-text-embed-v2`` model via
   Pinecone's Inference API.  The model natively produces larger vectors;
   Matryoshka slicing is used to truncate to 384 dimensions.

2. **Store embeddings** — upserts a ``(id, vector, metadata)`` tuple into
   the Pinecone index.  Metadata includes ``session_id``, ``type``
   (``"chat"`` or ``"memory"``), and the original text fields, enabling
   filtered retrieval.

3. **Search similar** — queries the index with a new embedding and returns
   the top-k most similar records, optionally filtered by ``session_id`` so
   that each conversation only retrieves its own history.

Graceful degradation
~~~~~~~~~~~~~~~~~~~~
If ``PINECONE_API_KEY`` is not set, or if the Pinecone client cannot be
initialised, ``is_available()`` returns ``False`` and all methods return
empty results.  The rest of the application falls back to PostgreSQL-only
memory retrieval.

Environment variables
~~~~~~~~~~~~~~~~~~~~~
``PINECONE_API_KEY``
    Required to enable Pinecone integration.
``PINECONE_ENVIRONMENT``
    AWS region of the serverless index (default: ``us-east-1``).
``PINECONE_INDEX_NAME``
    Name of the index to create/use (default: ``chatbot-memory``).
"""

import os

from dotenv import load_dotenv

load_dotenv()

import uuid
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from logging_config import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Pinecone vector database integration for embeddings.

    A single global instance (``vector_store``) is created at module import
    time.  All other modules should import and use that instance rather than
    instantiating this class directly.
    """

    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "chatbot-memory")

        # Model configuration
        self.model_name = "llama-text-embed-v2"
        self.output_dimension = 384

        self.pc = None
        self.index = None

        if self.api_key:
            self._initialize()

    def _initialize(self):
        """Initialize the Pinecone client and ensure the index exists.

        Creates a serverless index with cosine similarity metric if one with
        ``self.index_name`` does not already exist.  Any exception during
        initialisation is caught and printed; ``self.index`` remains ``None``
        so ``is_available()`` returns ``False``.
        """
        try:
            from pinecone import Pinecone, ServerlessSpec

            self.pc = Pinecone(api_key=self.api_key)

            # Create index if it doesn't exist
            if self.index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.output_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=self.environment),
                )

            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            logger.warning("Could not initialize Pinecone: %s", e)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def generate_embedding(self, text: str) -> list[float]:
        """Generate a 384-dimensional embedding for *text*.

        Uses the Pinecone Inference API with the ``llama-text-embed-v2``
        model.  The model supports Matryoshka Representation Learning, so the
        full vector is sliced to ``self.output_dimension`` (384) without
        retraining.

        Args:
            text: The input string to embed.

        Returns:
            A list of 384 floats, or an empty list if Pinecone is unavailable
            or an error occurs.
        """
        if not self.pc:
            return []
        embeddings = self.pc.inference.embed(
            model=self.model_name,
            inputs=[text],
            parameters={"input_type": "passage", "truncate": "END"},
        )
        full_vector = embeddings[0]["values"]
        return full_vector[: self.output_dimension]

    def store_embedding(self, text: str, metadata: dict[str, Any]) -> str:
        """Embed *text* and upsert the vector into the Pinecone index.

        Args:
            text: Raw text to embed (e.g. a concatenated message + response).
            metadata: Arbitrary key/value pairs stored alongside the vector
                for filtered retrieval.  At minimum, should contain
                ``session_id`` and ``type`` (``"chat"`` or ``"memory"``).

        Returns:
            The UUID string of the upserted vector, or an empty string if
            Pinecone is unavailable or the embedding could not be generated.
        """
        if not self.index:
            return ""

        vector_id = str(uuid.uuid4())
        embedding = self.generate_embedding(text)

        if embedding:
            self.index.upsert(vectors=[(vector_id, embedding, metadata)])

        return vector_id

    def search_similar(
        self, query: str, top_k: int = 5, filter: dict = None
    ) -> list[dict]:
        """Retrieve the most semantically similar vectors for *query*.

        Args:
            query: Natural-language query string to search with.
            top_k: Maximum number of results to return (default 5).
            filter: Optional Pinecone metadata filter dict, e.g.
                ``{"session_id": "abc-123"}`` to restrict results to a single
                conversation.

        Returns:
            A list of dicts, each with keys:

            - ``id`` (str): The Pinecone vector ID.
            - ``score`` (float): Cosine similarity score (higher = more similar).
            - ``metadata`` (dict): The metadata stored alongside the vector.

            Returns an empty list if Pinecone is unavailable or the query
            embedding could not be generated.
        """
        if not self.index:
            return []

        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return []

        results = self.index.query(
            vector=query_embedding, top_k=top_k, include_metadata=True, filter=filter
        )

        return [
            {"id": match.id, "score": match.score, "metadata": match.metadata}
            for match in results.matches
        ]

    def is_available(self) -> bool:
        """Return ``True`` if the Pinecone index was successfully initialised."""
        return self.index is not None


# Global instance
vector_store = VectorStore()
