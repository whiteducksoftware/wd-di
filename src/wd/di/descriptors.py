"""Service descriptors for wd-di.

This module defines :class:`ServiceDescriptor`, the immutable value object that stores
all metadata about a service registration. The container folds those factories
outside-in when it builds the final object, thereby enabling first-class decorator
support (see acceptance criteria A1–A4).
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, TypeVar, Generic, TYPE_CHECKING

from .lifetimes import ServiceLifetime

if TYPE_CHECKING:  # pragma: no cover
    # Forward import to avoid a circular reference on runtime.
    from .container import ServiceProvider

T = TypeVar("T")
DecoratorFactory = Callable[["ServiceProvider", Any], Any]
"""Callable that takes the current :class:`~wd.di.container.ServiceProvider` and the
*inner* instance and returns a (possibly) wrapped instance.  The return type is *Any*
on purpose to allow the decorator to change the runtime subtype while still respecting
the *semantic* contract of *T* at the call site.
"""


@dataclass(frozen=True, slots=True)
class ServiceDescriptor(Generic[T]):
    """Immutable description of a service registration.

    Attributes
    ----------
    service_type:
        The *abstraction* that clients request—usually an interface or base class.
    implementation_type:
        The concrete class that will be instantiated to satisfy the registration.
        Mutually exclusive with *factory*.
    factory:
        A callable that builds the instance given the current service provider.
        Mutually exclusive with *implementation_type*.
    lifetime:
        Controls how long the resulting object lives (transient, scoped, singleton).
    decorators:
        An *ordered* list of :data:`DecoratorFactory` objects to be applied to the
        instance after construction but **before** lifetime caching.
    """

    service_type: type[T]
    implementation_type: Optional[type] = None
    factory: Optional[Callable[["ServiceProvider"], T]] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    decorators: List[DecoratorFactory] = field(default_factory=list, repr=False, compare=False)

    # --------------------------------------------------------------------- #
    # Factory helpers
    # --------------------------------------------------------------------- #
    @classmethod
    def transient(
        cls,
        service_type: type[T],
        implementation_type: Optional[type] = None,
        factory: Optional[Callable[["ServiceProvider"], T]] = None,
    ) -> "ServiceDescriptor[T]":
        return cls(service_type, implementation_type, factory, ServiceLifetime.TRANSIENT)

    @classmethod
    def scoped(
        cls,
        service_type: type[T],
        implementation_type: Optional[type] = None,
        factory: Optional[Callable[["ServiceProvider"], T]] = None,
    ) -> "ServiceDescriptor[T]":
        return cls(service_type, implementation_type, factory, ServiceLifetime.SCOPED)

    @classmethod
    def singleton(
        cls,
        service_type: type[T],
        implementation_type: Optional[type] = None,
        factory: Optional[Callable[["ServiceProvider"], T]] = None,
    ) -> "ServiceDescriptor[T]":
        return cls(service_type, implementation_type, factory, ServiceLifetime.SINGLETON)

    # ------------------------------------------------------------------ #
    # Mutation helpers (return a *new* instance to keep immutability)
    # ------------------------------------------------------------------ #
    def with_decorator(self, decorator: DecoratorFactory) -> "ServiceDescriptor[T]":
        """Return a new descriptor with *decorator* appended to the chain.

        The method does **not** modify the original object (dataclass is frozen)
        but returns a new instance that shares all existing attributes.
        """
        return ServiceDescriptor(
            self.service_type,
            self.implementation_type,
            self.factory,
            self.lifetime,
            [*self.decorators, decorator],
        )

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #
    def __post_init__(self) -> None:
        if (self.implementation_type is None) == (self.factory is None):
            raise ValueError(
                "Exactly one of 'implementation_type' or 'factory' must be provided."
            )

        if self.decorators:
            # Ensure user did not accidentally pass a non-callable.
            for deco in self.decorators:
                if not callable(deco):
                    raise TypeError(
                        f"Decorator {deco!r} registered for {self.service_type.__name__} " 
                        "is not callable."
                    )

        if (
            self.implementation_type is not None
            and inspect.isabstract(self.implementation_type)
        ):
            raise TypeError(
                "implementation_type cannot be abstract; register the concrete class instead"
            )

__all__ = ["DecoratorFactory", "ServiceDescriptor"]
