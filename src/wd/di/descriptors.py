"""Service descriptors for the **wd-di** library.

This module defines the [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] class, which is an immutable
value object storing all metadata about a single service registration. It also
defines the [DecoratorFactory][wd.di.descriptors.DecoratorFactory] type alias, used for service decoration.

The [ServiceProvider][wd.di.container.ServiceProvider] uses these descriptors to instantiate and manage
services, applying any specified decorators in an outside-in order during object
creation. This mechanism enables first-class support for service decoration.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Generic, List, Optional, TypeVar

from .lifetimes import ServiceLifetime

if TYPE_CHECKING:  # pragma: no cover
    # Forward import to avoid a circular reference on runtime.
    from .container import ServiceProvider

T = TypeVar("T")
DecoratorFactory = Callable[["ServiceProvider", Any], Any]
"""A type alias for a decorator factory function.

This callable takes the current [ServiceProvider][wd.di.container.ServiceProvider] and the service
instance to be decorated (the *inner* instance) as arguments. It should return
a new instance, which may be a wrapped version of the original service.

The return type is `Any` to allow decorators the flexibility to change the
runtime subtype of the service, provided the new type still adheres to the
semantic contract of the original service type `T` expected by clients.

Args:
    ServiceProvider: The current [ServiceProvider][wd.di.container.ServiceProvider] instance.
    Any: The service instance to be decorated.

Returns:
    Any: The decorated (potentially wrapped) service instance.
"""


@dataclass(frozen=True, slots=True)
class ServiceDescriptor(Generic[T]):
    """An immutable description of a registered service.

    This data class holds all the necessary information about how a service
    should be instantiated, its lifetime, and any decorators that should be
    applied to it.

    Attributes:
        service_type (type[T]): The abstraction (usually an interface or base class)
            that clients will request from the [ServiceProvider][wd.di.container.ServiceProvider].
        implementation_type (Optional[type]): The concrete class that will be
            instantiated to satisfy the service request. This is mutually
            exclusive with `factory`.
        factory (Optional[Callable[[[ServiceProvider][wd.di.container.ServiceProvider]], T]]): A callable
            that, when invoked with the current [ServiceProvider][wd.di.container.ServiceProvider], returns an
            instance of the service. This is mutually exclusive with
            `implementation_type`.
        lifetime ([ServiceLifetime][wd.di.lifetimes.ServiceLifetime]): Specifies how long the service instance
            will live (e.g., transient, scoped, singleton).
        decorators (List[[DecoratorFactory][wd.di.descriptors.DecoratorFactory]]): An ordered list of decorator
            factories to be applied to the service instance after its initial
            construction but before it is cached according to its lifetime.
            Decorators are applied from first to last (outside-in).
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
        """Creates a new [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] with a transient lifetime.

        Args:
            service_type: The abstraction type of the service.
            implementation_type: The concrete implementation class. Optional if
                `factory` is provided.
            factory: A factory function to create the service instance. Optional
                if `implementation_type` is provided.

        Returns:
            A new [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] configured for a transient lifetime.
        """
        return cls(service_type, implementation_type, factory, ServiceLifetime.TRANSIENT)

    @classmethod
    def scoped(
        cls,
        service_type: type[T],
        implementation_type: Optional[type] = None,
        factory: Optional[Callable[["ServiceProvider"], T]] = None,
    ) -> "ServiceDescriptor[T]":
        """Creates a new [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] with a scoped lifetime.

        Args:
            service_type: The abstraction type of the service.
            implementation_type: The concrete implementation class. Optional if
                `factory` is provided.
            factory: A factory function to create the service instance. Optional
                if `implementation_type` is provided.

        Returns:
            A new [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] configured for a scoped lifetime.
        """
        return cls(service_type, implementation_type, factory, ServiceLifetime.SCOPED)

    @classmethod
    def singleton(
        cls,
        service_type: type[T],
        implementation_type: Optional[type] = None,
        factory: Optional[Callable[["ServiceProvider"], T]] = None,
    ) -> "ServiceDescriptor[T]":
        """Creates a new [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] with a singleton lifetime.

        Args:
            service_type: The abstraction type of the service.
            implementation_type: The concrete implementation class. Optional if
                `factory` is provided.
            factory: A factory function to create the service instance. Optional
                if `implementation_type` is provided.

        Returns:
            A new [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] configured for a singleton lifetime.
        """
        return cls(service_type, implementation_type, factory, ServiceLifetime.SINGLETON)

    # ------------------------------------------------------------------ #
    # Mutation helpers (return a *new* instance to keep immutability)
    # ------------------------------------------------------------------ #
    def with_decorator(self, decorator: DecoratorFactory) -> "ServiceDescriptor[T]":
        """Returns a new descriptor with the given decorator appended to its chain.

        Since [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] is immutable (frozen dataclass), this method
        does not modify the original object. Instead, it creates and returns a
        new [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] instance that includes the new decorator in
        addition to any existing ones.

        Args:
            decorator: The [DecoratorFactory][wd.di.descriptors.DecoratorFactory] to add to the service's
                decoration chain.

        Returns:
            A new [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] instance with the decorator added.
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
        """Performs validation checks after the descriptor is initialized.

        Ensures that:
        1. Exactly one of `implementation_type` or `factory` is provided.
        2. All registered decorators are callable.
        3. The `implementation_type` (if provided) is not an abstract class.

        Raises:
            ValueError: If the mutual exclusivity of `implementation_type` and
                `factory` is violated.
            TypeError: If a registered decorator is not callable, or if
                `implementation_type` is an abstract class.
        """
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
