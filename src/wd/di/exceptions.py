"""Custom exception hierarchy for the **wd-di** library.

This module defines domain-specific exceptions used by the dependency injection
container. These custom exceptions provide clearer, more actionable feedback to
users compared to generic `RuntimeError` instances.

Public Classes:
    InvalidOperationError: Raised when an action is attempted that is invalid
        for the current state of an object (e.g., modifying a
        [ServiceCollection][wd.di.service_collection.ServiceCollection] after its
        [ServiceProvider][wd.di.container.ServiceProvider] has been built).
    CircularDecoratorError: Raised during the provider-building phase if a
        circular dependency is detected among service decorators.

Both exception types inherit from `RuntimeError`, ensuring that existing error
handling for general runtime issues remains effective.
"""

from __future__ import annotations

from typing import Sequence

__all__ = [
    "CircularDecoratorError",
    "InvalidOperationError",
]


class InvalidOperationError(RuntimeError):
    """Indicates an operation is attempted that is not valid for the object's current state."""


class CircularDecoratorError(RuntimeError):
    """Indicates a cycle was detected in the chain of service decorators.

    This error is raised when the [ServiceProvider][wd.di.container.ServiceProvider] is being built and it discovers
    that two or more decorators reference each other in a circular manner
    (e.g., Decorator A wraps Decorator B, and Decorator B wraps Decorator A).

    Attributes:
        chain (List[str | type | object]): The sequence of decorator callables or
            classes that form the detected cycle, in the order they were traversed.
            This can be used to help identify and resolve the circular dependency.
    """

    def __init__(self, chain: Sequence[str | type | object]):
        """Initializes a new CircularDecoratorError instance.

        Args:
            chain: The sequence of decorator callables or classes involved in the cycle.
        """
        pretty_chain = " \u2192 ".join(_name(c) for c in chain)  # arrows between names
        super().__init__(f"Circular decorator chain detected: {pretty_chain}")
        self.chain = list(chain)


# ---------------------------------------------------------------------- #
# Helper - derive a human-readable name for a decorator object
# ---------------------------------------------------------------------- #

def _name(obj: object) -> str:  # pragma: no cover - pure formatting
    """Derives a human-readable name for a decorator object.

    Used internally to generate informative error messages for
    [CircularDecoratorError][wd.di.exceptions.CircularDecoratorError].

    Args:
        obj: The object (typically a function, class, or instance) from which
            to derive a name.

    Returns:
        A string representing the name of the object. It attempts to use
        `__qualname__`, then `__name__`, and falls back to `repr(obj)` if
        neither is available.
    """
    if hasattr(obj, "__qualname__"):
        return obj.__qualname__  # type: ignore[attr-defined]
    if hasattr(obj, "__name__"):
        return obj.__name__  # type: ignore[attr-defined]
    return repr(obj)
