"""
Common interfaces that the rest of the code depends on.
"""

from abc import ABC, abstractmethod
from typing import Protocol


class IBlobStorage(ABC):
    """Abstract storage service — backend-agnostic."""

    @abstractmethod
    def upload(self, path: str, data: bytes) -> str:
        """Uploads `data` and returns a URI to the stored object."""
        ...


class IClock(Protocol):
    """Cross-cutting dependency used for timestamping URIs."""

    def now(self): ...
