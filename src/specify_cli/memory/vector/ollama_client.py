"""
Ollama embeddings client for vector memory.

Generates embeddings using Ollama mxbai-embed-large model.
"""

import requests
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..logging import get_logger


class OllamaClient:
    """Client for Ollama embeddings API."""

    # Default configuration
    DEFAULT_HOST = "http://localhost:11434"
    DEFAULT_MODEL = "mxbai-embed-large"
    EMBEDDING_DIM = 1024  # mxbai-embed-large produces 1024-dim vectors
    TIMEOUT = 30  # seconds

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = TIMEOUT
    ):
        """Initialize Ollama client.

        Args:
            host: Ollama host URL (default: localhost:11434)
            model: Model name (default: mxbai-embed-large)
            timeout: Request timeout in seconds
        """
        self.logger = get_logger()
        self.host = host or self.DEFAULT_HOST
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
        self.embed_url = f"{self.host}/api/embed"
        self.tags_url = f"{self.host}/api/tags"

    def is_available(self) -> bool:
        """Check if Ollama service is available.

        Returns:
            True if Ollama is responding
        """
        try:
            response = requests.get(
                self.tags_url,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def is_model_available(self) -> bool:
        """Check if the embedding model is available.

        Returns:
            True if model is installed
        """
        try:
            response = requests.get(
                self.tags_url,
                timeout=5
            )

            if response.status_code != 200:
                return False

            data = response.json()
            models = data.get("models", [])

            return any(
                m.get("name", "").startswith(self.model)
                for m in models
            )

        except Exception:
            return False

    def embed(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector or None if failed
        """
        if not text or not text.strip():
            return None

        try:
            payload = {
                "model": self.model,
                "input": text.strip()
            }

            response = requests.post(
                self.embed_url,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code != 200:
                self.logger.warning(f"Ollama error: {response.status_code}")
                return None

            data = response.json()

            # Extract embedding
            if "embedding" in data:
                return data["embedding"]
            elif "embeddings" in data and len(data["embeddings"]) > 0:
                return data["embeddings"][0]

            return None

        except requests.Timeout:
            self.logger.warning(f"Ollama timeout after {self.timeout}s")
            return None
        except Exception as e:
            self.logger.warning(f"Ollama embed error: {e}")
            return None

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts
            batch_size: Number of texts per request

        Returns:
            List of embedding vectors (None for failed)
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Try batch request first
            batch_embeddings = self._embed_batch_request(batch)

            if batch_embeddings is None:
                # Fallback to individual requests
                for text in batch:
                    embedding = self.embed(text)
                    results.append(embedding)
            else:
                results.extend(batch_embeddings)

            # Small delay to avoid overwhelming Ollama
            if i + batch_size < len(texts):
                time.sleep(0.1)

        return results

    def _embed_batch_request(self, texts: List[str]) -> Optional[List[Optional[List[float]]]]:
        """Attempt batch embedding request.

        Args:
            texts: List of texts

        Returns:
            List of embeddings or None if batch failed
        """
        if not texts:
            return []

        try:
            payload = {
                "model": self.model,
                "input": [t.strip() for t in texts if t and t.strip()]
            }

            if not payload["input"]:
                return [None] * len(texts)

            response = requests.post(
                self.embed_url,
                json=payload,
                timeout=self.timeout * 2  # Longer timeout for batch
            )

            if response.status_code != 200:
                return None

            data = response.json()

            if "embeddings" in data:
                return data["embeddings"]

            return None

        except Exception:
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get Ollama service status.

        Returns:
            Dict with status information
        """
        status = {
            "available": self.is_available(),
            "host": self.host,
            "model": self.model,
            "model_available": False,
            "embedding_dim": self.EMBEDDING_DIM
        }

        if status["available"]:
            status["model_available"] = self.is_model_available()

        return status
