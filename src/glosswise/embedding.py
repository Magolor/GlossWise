"""Context-bound embedding adapter."""

from __future__ import annotations

__all__ = ["HeavenBaseEmbedder"]

from collections.abc import Sequence
from typing import Any

import heavenbase as hb

from .errors import GlossWiseError


class HeavenBaseEmbedder:
    """Adapt one explicit HeavenBase LLM client to GlossWise vectors.

    Args:
        context (hb.Context): Owning machine Context.
        embedding_space (str): Immutable model/revision/normalization id.
        dimension (int): Required GlossWise vector dimension.
        preset (str | None): Optional HeavenBase LLM preset.
        model (str | None): Optional explicit model.
        provider (str | None): Optional explicit provider.
        gateway (str | None): Optional explicit gateway.
        **kwargs (Any): Additional `hb.LLM` construction arguments.
    """

    def __init__(
        self,
        context: hb.Context,
        *,
        embedding_space: str,
        dimension: int,
        preset: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        gateway: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Construct one Context-authoritative embedding adapter."""
        self.context = context
        self.embedding_space = str(embedding_space)
        self.dimension = int(dimension)
        self.client = hb.LLM(
            preset=preset,
            model=model,
            provider=provider,
            gateway=gateway,
            context=context,
            **kwargs,
        )

    @classmethod
    def mock(
        cls,
        context: hb.Context,
        *,
        embedding_space: str = "mock/deterministic/1",
        dimension: int = 3,
    ) -> "HeavenBaseEmbedder":
        """Create the deterministic offline HeavenBase mock adapter.

        Args:
            context (hb.Context): Owning machine Context.
            embedding_space (str): Fixture embedding-space id.
            dimension (int): Fixture vector dimension.

        Returns:
            HeavenBaseEmbedder: Network-free adapter using `gateway="mock"`.
        """
        return cls(
            context,
            embedding_space=embedding_space,
            dimension=dimension,
            preset="mock",
            gateway="mock",
            cache=False,
            mock={"embed_dim": dimension},
        )

    def embed(self, inputs: Sequence[str]) -> list[list[float]]:
        """Embed a non-empty batch and validate every returned vector.

        Args:
            inputs (Sequence[str]): Texts in caller order.

        Returns:
            list[list[float]]: Concrete vectors in the configured space.

        Raises:
            GlossWiseError: If the provider fails or returns incompatible
                output.
        """
        texts = [str(item) for item in inputs]
        if not texts:
            return []
        try:
            raw = self.client.embed(texts)
        except Exception as error:
            raise GlossWiseError(
                "embedding_unavailable",
                "The configured embedding provider could not complete the request.",
            ) from error
        vectors = [list(vector) for vector in raw]
        if len(vectors) != len(texts) or any(len(vector) != self.dimension for vector in vectors):
            raise GlossWiseError(
                "embedding_space_mismatch",
                "The embedding provider returned an incompatible vector shape.",
            )
        try:
            return [[float(value) for value in vector] for vector in vectors]
        except (TypeError, ValueError) as error:
            raise GlossWiseError(
                "embedding_space_mismatch",
                "The embedding provider returned a non-numeric vector.",
            ) from error
