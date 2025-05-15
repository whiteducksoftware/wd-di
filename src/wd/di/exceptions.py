"""Custom exception hierarchy for **wd-di**.

The container uses a handful of domain-specific errors to give end-users clear,
actionable feedback instead of generic `RuntimeError`s.

Public classes
--------------
* :class:`InvalidOperationError` – raised when the caller performs an action
  that is not allowed in the current container state, e.g. mutating a
  :class:`~wd.di.service_collection.ServiceCollection` *after* the provider has
  been built.
* :class:`CircularDecoratorError` – raised at provider-build time when two or
  more decorators form a cycle (A ↔ B ↔ … ↔ A).  The error message includes the
  discovered chain to help users debug the registration.

Both errors inherit from :class:`RuntimeError` so existing `except` blocks that
catch generic runtime container issues continue to work.
"""

from __future__ import annotations

from typing import Sequence

__all__ = [
    "InvalidOperationError",
    "CircularDecoratorError",
]


class InvalidOperationError(RuntimeError):
    """Raised when an operation is not valid for the object’s state."""


class CircularDecoratorError(RuntimeError):
    """Raised when a cycle in the decorator chain is detected.

    Parameters
    ----------
    chain:
        The list of decorator callables/classes involved in the cycle, in the
        order they were traversed.
    """

    def __init__(self, chain: Sequence[str | type | object]):
        pretty_chain = " \u2192 ".join(_name(c) for c in chain)  # arrows between names
        super().__init__(f"Circular decorator chain detected: {pretty_chain}")
        self.chain = list(chain)


# ---------------------------------------------------------------------- #
# Helper – derive a human-readable name for a decorator object
# ---------------------------------------------------------------------- #

def _name(obj: object) -> str:  # pragma: no cover – pure formatting
    if hasattr(obj, "__qualname__"):
        return obj.__qualname__  # type: ignore[attr-defined]
    if hasattr(obj, "__name__"):
        return obj.__name__  # type: ignore[attr-defined]
    return repr(obj)