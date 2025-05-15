"""Service registration API for **wd-di** (decorator‑aware).

This module exposes the fluent DSL that users employ at *composition‑root* time
to wire up their application.  It now supports *decorators* via
:meth:`ServiceCollection.decorate` while **retaining every public helper** that
existed in previous releases:

* `add_instance`, `add_*` for class registrations, `add_*_factory` for factory
  registrations
* `configure` to bind strongly‑typed *Options* objects from an
  `IConfiguration` source
* Python‑level class decorators: `@services.singleton`, `@services.scoped`,
  `@services.transient`

No user code must change; the new API is purely additive.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, List, Optional, Type, TypeVar, Generic, TYPE_CHECKING, overload

from .descriptors import DecoratorFactory, ServiceDescriptor
from .lifetimes import ServiceLifetime
from .exceptions import InvalidOperationError
from .config import IConfiguration, Options, OptionsBuilder

if TYPE_CHECKING:  # pragma: no cover
    from .container import ServiceProvider

__all__ = ["ServiceCollection"]

T = TypeVar("T")
S = TypeVar("S")  # service/abstraction type for decorator overloads


class ServiceCollection(Generic[T]):
    """Collects :class:`~wd.di.descriptors.ServiceDescriptor` objects and builds a provider."""

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    def __init__(self, descriptors: Optional[Iterable[ServiceDescriptor[Any]]] = None):
        self._services: List[ServiceDescriptor[Any]] = list(descriptors) if descriptors else []
        self._is_built: bool = False

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #
    def _ensure_not_built(self) -> None:
        if self._is_built:
            raise InvalidOperationError(
                "Cannot modify ServiceCollection after ServiceProvider has been built."
            )

    def _add(
        self,
        lifetime: ServiceLifetime,
        service_type: Type[Any],
        implementation_type: Optional[Type[Any]] = None,
        factory: Optional[Callable[["ServiceProvider"], Any]] = None,
    ) -> "ServiceCollection":
        """Create & store a :class:`ServiceDescriptor` (internal helper).

        If the caller omits both *implementation_type* and *factory* we assume a
        *self‑binding* registration (``implementation_type = service_type``) to
        preserve legacy behaviour.
        """
        self._ensure_not_built()

        if implementation_type is None and factory is None:
            implementation_type = service_type

        descriptor = ServiceDescriptor(
            service_type,
            implementation_type,
            factory,
            lifetime,
        )
        self._services.append(descriptor)
        return self  # fluent API

    # ------------------------------------------------------------------ #
    # Public API – registrations (class or factory)
    # ------------------------------------------------------------------ #
    def add_transient(
        self,
        service_type: Type[Any],
        implementation_type: Optional[Type[Any]] = None,
        factory: Optional[Callable[["ServiceProvider"], Any]] = None,
    ) -> "ServiceCollection":
        return self._add(ServiceLifetime.TRANSIENT, service_type, implementation_type, factory)

    def add_scoped(
        self,
        service_type: Type[Any],
        implementation_type: Optional[Type[Any]] = None,
        factory: Optional[Callable[["ServiceProvider"], Any]] = None,
    ) -> "ServiceCollection":
        return self._add(ServiceLifetime.SCOPED, service_type, implementation_type, factory)

    def add_singleton(
        self,
        service_type: Type[Any],
        implementation_type: Optional[Type[Any]] = None,
        factory: Optional[Callable[["ServiceProvider"], Any]] = None,
    ) -> "ServiceCollection":
        return self._add(ServiceLifetime.SINGLETON, service_type, implementation_type, factory)

    # ------------------------------------------------------------------ #
    # Convenience – direct instance
    # ------------------------------------------------------------------ #
    def add_instance(self, service_type: Type[Any], instance: Any) -> "ServiceCollection":
        """Register an *already‑constructed* singleton instance."""
        self._ensure_not_built()

        def _factory(_: "ServiceProvider") -> Any:  # noqa: D401 – simple stub
            return instance

        descriptor = ServiceDescriptor(
            service_type,
            factory=_factory,
            lifetime=ServiceLifetime.SINGLETON,
        )
        self._services.append(descriptor)
        return self

    # ------------------------------------------------------------------ #
    # Convenience – explicit factory overloads
    # ------------------------------------------------------------------ #
    def add_transient_factory(
        self,
        service_type: Type[Any],
        factory: Callable[["ServiceProvider"], Any],
    ) -> "ServiceCollection":
        return self._add(ServiceLifetime.TRANSIENT, service_type, factory=factory)

    def add_scoped_factory(
        self,
        service_type: Type[Any],
        factory: Callable[["ServiceProvider"], Any],
    ) -> "ServiceCollection":
        return self._add(ServiceLifetime.SCOPED, service_type, factory=factory)

    def add_singleton_factory(
        self,
        service_type: Type[Any],
        factory: Callable[["ServiceProvider"], Any],
    ) -> "ServiceCollection":
        return self._add(ServiceLifetime.SINGLETON, service_type, factory=factory)

    # ------------------------------------------------------------------ #
    # Options / configuration support
    # ------------------------------------------------------------------ #
    def configure(self, options_type: Type[T], *, section: Optional[str] = None) -> "ServiceCollection":
        """Bind *options_type* from the shared :pydata:`IConfiguration` instance.

        ``services.configure(MySettings)`` automatically registers
        ``Options[MySettings]`` as a singleton whose value is built by binding
        *MySettings* against the configuration tree at provider‑build time.
        """
        self._ensure_not_built()

        def _factory(sp: "ServiceProvider") -> Options[T]:  # runtime generic
            try:
                configuration = sp.get_service(IConfiguration)
            except Exception as exc:  # pragma: no cover – defensive
                raise Exception("IConfiguration service not registered") from exc

            builder = OptionsBuilder(options_type)
            builder.bind_configuration(configuration, section)
            return Options(builder.build())

        # Register an *open‑generic* Options[...] singleton.
        self.add_singleton_factory(Options[options_type], _factory)  # type: ignore[index]
        return self

    # ------------------------------------------------------------------ #
    # Python‑level decorators – syntactic sugar
    # ------------------------------------------------------------------ #
    # Singleton -------------------------------------------------------- #
    @overload
    def singleton(self) -> Callable[[Type[T]], Type[T]]: ...

    @overload
    def singleton(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def singleton(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:  # type: ignore[override]
        def _decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_singleton(impl, impl)
            else:
                self.add_singleton(service_type, impl)  # type: ignore[arg-type]
            return impl

        return _decorator

    # Scoped ----------------------------------------------------------- #
    @overload
    def scoped(self) -> Callable[[Type[T]], Type[T]]: ...

    @overload
    def scoped(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def scoped(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:  # type: ignore[override]
        def _decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_scoped(impl, impl)
            else:
                self.add_scoped(service_type, impl)  # type: ignore[arg-type]
            return impl

        return _decorator

    # Transient -------------------------------------------------------- #
    @overload
    def transient(self) -> Callable[[Type[T]], Type[T]]: ...

    @overload
    def transient(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def transient(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:  # type: ignore[override]
        def _decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_transient(impl, impl)
            else:
                self.add_transient(service_type, impl)  # type: ignore[arg-type]
            return impl

        return _decorator

    # ------------------------------------------------------------------ #
    # Public API – decorator support (service *wrappers*)
    # ------------------------------------------------------------------ #
    def decorate(self, service_type: Type[Any], decorator: DecoratorFactory) -> "ServiceCollection":
        self._ensure_not_built()

        for idx, descriptor in enumerate(self._services):
            if descriptor.service_type is service_type:
                self._services[idx] = descriptor.with_decorator(decorator)
                break
        else:  # pragma: no cover
            raise KeyError(
                f"No service registered for {service_type.__name__!s}; cannot apply decorator."
            )

        return self

    # ------------------------------------------------------------------ #
    # Build provider
    # ------------------------------------------------------------------ #
    def build_service_provider(self) -> "ServiceProvider":
        from .container import ServiceProvider  # local import avoids heavy cost when only building collections

        self._is_built = True
        return ServiceProvider(self._services)

    # ------------------------------------------------------------------ #
    # Introspection helpers
    # ------------------------------------------------------------------ #
    def __iter__(self):
        return iter(self._services)

    def __len__(self) -> int:  # type: ignore[override]
        return len(self._services)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ServiceCollection services={len(self)} built={self._is_built}>"
