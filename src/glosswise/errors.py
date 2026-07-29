"""Stable GlossWise domain errors."""

from __future__ import annotations

__all__ = ["GlossWiseError", "is_glosswise_error"]

from collections.abc import Sequence


class GlossWiseError(Exception):
    """Report a caller-actionable GlossWise failure.

    Args:
        code (str): Stable machine-readable error code.
        message (str): Redacted caller-facing explanation.
        object_ids (Sequence[str]): Optional related object identities.
    """

    error_type = "glosswise.error/v1"

    def __init__(
        self,
        code: str,
        message: str,
        *,
        object_ids: Sequence[str] = (),
    ) -> None:
        """Create a stable domain error.

        Args:
            code (str): Stable machine-readable error code.
            message (str): Redacted caller-facing explanation.
            object_ids (Sequence[str]): Optional related object identities.

        Returns:
            None: This initializer stores the error contract.
        """
        super().__init__(message)
        self.code = str(code)
        self.message = str(message)
        self.object_ids = tuple(str(item) for item in object_ids)

    def to_dict(self) -> dict[str, object]:
        """Return the serializable redacted error contract.

        Args:
            None.

        Returns:
            dict[str, object]: Error code, message, and related object ids.
        """
        return {
            "code": self.code,
            "message": self.message,
            "object_ids": list(self.object_ids),
        }


def is_glosswise_error(error: BaseException) -> bool:
    """Recognize errors across HeavenBase artifact-loader generations.

    HeavenBase restores captured extension code under generation-local module
    names, so class identity is not stable across the package and an activated
    extension API. The explicit marker preserves a narrow public predicate.

    Args:
        error (BaseException): Exception raised by a package or captured API.

    Returns:
        bool: Whether the exception implements the GlossWise error contract.
    """
    return (
        getattr(error, "error_type", None) == GlossWiseError.error_type
        and isinstance(getattr(error, "code", None), str)
        and callable(getattr(error, "to_dict", None))
    )
