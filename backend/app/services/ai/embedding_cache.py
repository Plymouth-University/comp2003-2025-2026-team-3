"""
Embedding Cache Module

Caches ticket embeddings to avoid re-encoding the same text.
Uses LRU cache with TTL to manage memory usage.
"""

import hashlib
import time
from typing import Optional
import torch
import logging

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    LRU cache for ticket embeddings with TTL (time-to-live).

    Avoids re-encoding tickets that have already been processed.
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize embedding cache.

        Args:
            max_size: Maximum number of embeddings to cache
            ttl_seconds: Time-to-live for cached embeddings (default 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}  # {text_hash: (embedding, timestamp)}
        self.access_order = []  # For LRU tracking
        self.hits = 0
        self.misses = 0

    def _hash_text(self, text: str) -> str:
        """Create fast hash of text for cache key."""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> Optional[torch.Tensor]:
        """
        Get cached embedding if available and not expired.

        Args:
            text: Ticket text

        Returns:
            Cached embedding or None if not found/expired
        """
        text_hash = self._hash_text(text)

        if text_hash in self.cache:
            embedding, timestamp = self.cache[text_hash]

            # Check if expired
            if time.time() - timestamp > self.ttl_seconds:
                del self.cache[text_hash]
                self.access_order.remove(text_hash)
                self.misses += 1
                return None

            # Update access order (move to end = most recently used)
            self.access_order.remove(text_hash)
            self.access_order.append(text_hash)

            self.hits += 1
            return embedding

        self.misses += 1
        return None

    def get_batch(self, texts: list[str]) -> tuple[list[torch.Tensor], list[int]]:
        """
        Get cached embeddings for a batch of texts.

        Args:
            texts: List of ticket texts

        Returns:
            Tuple of (cached_embeddings, indices_needing_encoding)
            where cached_embeddings has None for texts that need encoding
        """
        cached_embeddings = []
        indices_needing_encoding = []

        for i, text in enumerate(texts):
            embedding = self.get(text)
            if embedding is None:
                indices_needing_encoding.append(i)
            cached_embeddings.append(embedding)

        return cached_embeddings, indices_needing_encoding

    def put(self, text: str, embedding: torch.Tensor):
        """
        Store embedding in cache.

        Args:
            text: Ticket text
            embedding: Computed embedding
        """
        text_hash = self._hash_text(text)

        # Enforce max size (LRU eviction)
        if text_hash not in self.cache and len(self.cache) >= self.max_size:
            # Remove least recently used
            oldest = self.access_order.pop(0)
            del self.cache[oldest]

        # Store with current timestamp
        self.cache[text_hash] = (embedding, time.time())

        # Update access order
        if text_hash in self.access_order:
            self.access_order.remove(text_hash)
        self.access_order.append(text_hash)

    def put_batch(self, texts: list[str], embeddings: torch.Tensor):
        """
        Store multiple embeddings at once.

        Args:
            texts: List of ticket texts
            embeddings: Tensor of embeddings [batch_size, embedding_dim]
        """
        for i, text in enumerate(texts):
            self.put(text, embeddings[i])

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl_seconds": self.ttl_seconds,
        }

    def clear(self):
        """Clear the entire cache."""
        self.cache.clear()
        self.access_order.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Embedding cache cleared")


# Global cache instance
_embedding_cache = EmbeddingCache(max_size=1000, ttl_seconds=3600)


def get_cache() -> EmbeddingCache:
    """Get the global embedding cache instance."""
    return _embedding_cache
