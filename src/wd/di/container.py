"""Runtime service provider for the **wd-di** library.

This module provides the [ServiceProvider][wd.di.container.ServiceProvider] class, which is the runtime
component responsible for resolving service instances based on registrations made
in a [ServiceCollection][wd.di.service_collection.ServiceCollection].

Key features include:
    - Resolution of services according to their specified lifetimes (transient,
      scoped, singleton).
    - Caching of singleton and scoped services.
    - Creation of new scopes for managing scoped service instances.
    - First-class support for decorator application, where decorators are folded
      around the core service instance during resolution.
    - Detection of circular dependencies during service resolution, including those
      caused by decorators, using a task-local resolution stack.

The [ServiceProvider][wd.di.container.ServiceProvider] maintains backward compatibility with previous versions,
supporting initialization with both dictionary-based and list-based collections
of [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] objects. The [Scope][wd.di.container.Scope] alias is also provided
for compatibility with older import paths.
"""

from __future__ import annotations

import contextvars
import inspect
import threading
from typing import Any, Dict, List, Mapping, Sequence, Type, TypeVar, Union, get_type_hints, overload

from .descriptors import ServiceDescriptor
from .exceptions import CircularDecoratorError, InvalidOperationError
from .lifetimes import ServiceLifetime

__all__ = ["Scope", "ServiceProvider"]

T = TypeVar("T")

# --------------------------------------------------------------------------- #
# Task-local resolution stack (dependency & decorator cycles)
# --------------------------------------------------------------------------- #

_resolution_stack: contextvars.ContextVar[List[str]] = contextvars.ContextVar(
    "wd_di_resolution_stack", default=[]
)
"""A context variable holding a list of service keys currently being resolved.

This stack is used to detect circular dependencies during service resolution.
Each string in the list is a unique key representing a service or decorator
(see `_key` function). Before resolving a service or applying a decorator,
its key is added to this stack. If the key is already present, a circular
dependency is detected.
"""


class ServiceProvider:
    """The runtime dependency injection container that resolves service instances.

    A [ServiceProvider][wd.di.container.ServiceProvider] is built from a [ServiceCollection][wd.di.service_collection.ServiceCollection]
    and is responsible for creating and managing the lifecycle of services.

    Attributes:
        _root ([ServiceProvider][wd.di.container.ServiceProvider]): The root service provider. For a root provider, this
            is a reference to itself. For a scoped provider, this is a reference
            to the root provider from which the scope was created.
        _descriptors (Dict[Type[Any], [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor][Any]]): A dictionary mapping
            service types to their corresponding [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] objects.
        _singleton_cache (Dict[Type[Any], Any]): A cache for singleton service
            instances. Shared between the root provider and all its scopes.
        _singleton_lock (threading.RLock): A reentrant lock to synchronize access
            to the `_singleton_cache`.
        _scoped_cache (Dict[Type[Any], Any]): A cache for scoped service instances.
            Each scope (including the root provider, which acts as its own scope)
            has its own independent scoped cache.
        _disposables (List[Any]): A list of disposable service instances created
            within the current scope. These are disposed of when the scope itself
            is disposed.
    """
    # NOTE: 'services' can be a mapping (old API) **or** a list (new API)
    def __init__(
        self,
        services: Union[Sequence[ServiceDescriptor[Any]], Mapping[Type[Any], ServiceDescriptor[Any]]],
        *,
        _root: "ServiceProvider | None" = None,
    ) -> None:
        """Initializes a new ServiceProvider instance.

        This constructor handles both root provider creation and scoped provider
        creation. Scoped providers are typically created via the `create_scope`
        method.

        Args:
            services: A collection of [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] objects. Can be either a
                sequence (list, tuple) of descriptors (new API) or a mapping
                from service types to descriptors (old API for backward compatibility).
            _root: For internal use. If provided, this provider becomes a scope of
                the specified `_root` provider. If `None`, this provider is a new
                root provider.
        """
        # ------------------------------------------------------------------ #
        # Root vs scope initialisation
        # ------------------------------------------------------------------ #
        if _root is None:  # root provider (publicly constructed)
            self._root: "ServiceProvider" = self

            # Accept both old dict-based and new list-based descriptor stores.
            if isinstance(services, Mapping):
                self._descriptors: Dict[Type[Any], ServiceDescriptor[Any]] = dict(services)
            else:
                self._descriptors = {d.service_type: d for d in services}

            self._singleton_cache: Dict[Type[Any], Any] = {}
            self._singleton_lock = threading.RLock()
        else:  # scoped provider (private constructor via create_scope)
            self._root = _root
            # Re-use the root's descriptors & singleton cache.
            self._descriptors = _root._descriptors
            self._singleton_cache = _root._singleton_cache
            self._singleton_lock = _root._singleton_lock

        # Each scope (including root) gets its *own* scoped cache & disposables.
        self._scoped_cache: Dict[Type[Any], Any] = {}
        self._disposables: List[Any] = []

    # ------------------------------------------------------------------ #
    # Public API – resolve service
    # ------------------------------------------------------------------ #
    @overload
    def get_service(self, service_type: Type[T]) -> T: ...

    @overload
    def get_service(self, service_type: Type[Any]) -> Any: ...

    def get_service(self, service_type: Type[Any]):  # type: ignore[override]
        """Resolves an instance of the requested service type.

        This method handles the creation and caching of services based on their
        registered [ServiceLifetime][wd.di.lifetimes.ServiceLifetime]. It also detects circular dependencies.

        Args:
            service_type: The type of the service to resolve.

        Returns:
            An instance of the requested `service_type`.

        Raises:
            KeyError: If no service is registered for `service_type`.
            [InvalidOperationError][wd.di.exceptions.InvalidOperationError]: If a scoped service is requested from the
                root provider without creating a scope first.
            [CircularDecoratorError][wd.di.exceptions.CircularDecoratorError]: If a circular dependency involving
                decorators is detected during resolution.
            RuntimeError: If a general circular dependency (not involving decorators,
                or not identifiable as such by the decorator cycle check) is detected.
        """
        desc = self._descriptors.get(service_type)
        if desc is None:
            raise KeyError(f"No service registered for type {service_type!r}.")

        # ---------- fast path: cache lookup ----------
        if desc.lifetime is ServiceLifetime.SINGLETON:
            try:
                return self._singleton_cache[service_type]
            except KeyError:
                pass  # miss → build
        elif desc.lifetime is ServiceLifetime.SCOPED:
            # Check if attempting to resolve a scoped service from the root provider
            if self._root is self: # We are the root provider
                raise InvalidOperationError(
                    "Cannot resolve scoped service from the root provider. "
                    "Please create a scope using 'create_scope()' and resolve it from the scope."
                )
            try:
                return self._scoped_cache[service_type]
            except KeyError:
                pass
        # Transient → always build.

        # ---------- circular dependency guard ----------
        stack = _resolution_stack.get()
        frame = _key(service_type)

        if frame in stack:
            idx_frame_in_stack = stack.index(frame)

            # Check if this is a decorator-induced cycle:
            # Service S is being resolved, its decorator D is invoked, and D (or its dependencies)
            # tries to resolve S again.
            # Stack would be: [..., S_key, D_key_for_S, ... (possibly other things if D calls other services)],
            # and now 'frame' (S_key) is being requested again.
            # 'desc' is the ServiceDescriptor for 'service_type' (whose key is 'frame').
            if desc and desc.decorators and (idx_frame_in_stack + 1) < len(stack):
                item_after_frame_in_stack = stack[idx_frame_in_stack + 1]
                # These are the keys of decorators registered for the current service 'frame'.
                decorator_keys_for_this_service = {_key(deco_factory) for deco_factory in desc.decorators}

                if item_after_frame_in_stack in decorator_keys_for_this_service:
                    # The cycle is: frame -> item_after_frame (a decorator for frame) -> ... -> frame (current request)
                    # This indicates the decorator 'item_after_frame_in_stack' (or something it called)
                    # is trying to resolve 'frame' again.
                    cycle_path = stack[idx_frame_in_stack:] + [frame]
                    raise CircularDecoratorError(cycle_path)

            # If not a decorator cycle identified above, then it's a general circular dependency.
            cycle_path = stack[idx_frame_in_stack:] + [frame]
            raise RuntimeError("Circular dependency detected: " + " -> ".join(cycle_path))

        stack.append(frame)
        _resolution_stack.set(stack)
        try:
            instance = self._create_instance(desc)
        finally:
            stack.pop()

        # ---------- lifetime caching ----------
        if desc.lifetime is ServiceLifetime.SINGLETON:
            with self._singleton_lock:
                if service_type not in self._singleton_cache:  # double-checked
                    self._singleton_cache[service_type] = instance
        elif desc.lifetime is ServiceLifetime.SCOPED:
            self._scoped_cache[service_type] = instance
            self._try_register_disposable(instance)
        # Transient → caller owns the object.

        return instance  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Scoping
    # ------------------------------------------------------------------ #
    def create_scope(self) -> "ServiceProvider":
        """Creates a new scope from this service provider.

        The new scope is a new [ServiceProvider][wd.di.container.ServiceProvider] instance that shares the same
        service descriptors and singleton cache as the root provider but has its
        own independent cache for scoped services. Scoped services resolved within
        this new scope will live as long as the scope itself.

        Returns:
            A new [ServiceProvider][wd.di.container.ServiceProvider] instance representing the created scope.
        """
        return ServiceProvider([], _root=self._root)

    # ------------------------------------------------------------------ #
    # Disposal (scoped provider)
    # ------------------------------------------------------------------ #
    def dispose(self):
        """Disposes of this scope and all disposable services created within it.

        This method is primarily relevant for scoped service providers. It iterates
        through all tracked disposable instances created within the scope and calls
        their `dispose()` or `close()` method if available. After disposing of the
        instances, it clears the scope's cache and the list of disposables.

        Calling `dispose()` on a root provider typically has no effect on its own
        scoped cache or disposables, as these are managed by dedicated scopes.
        However, singletons are managed by the root and are not disposed of via
        this scope disposal mechanism.
        """
        for inst in self._disposables:
            if hasattr(inst, "dispose") and callable(inst.dispose):
                try:
                    inst.dispose()
                except Exception as exc:
                    print(f"Error disposing {inst}: {exc}")
            elif hasattr(inst, "close") and callable(inst.close):
                try:
                    inst.close()
                except Exception as exc:
                    print(f"Error closing {inst}: {exc}")
        self._disposables.clear()
        self._scoped_cache.clear()

    # Context-manager support (for 'with' blocks)
    def __enter__(self):
        """Enables the use of a [ServiceProvider][wd.di.container.ServiceProvider] (typically a scope) as a context manager.

        Returns:
            The [ServiceProvider][wd.di.container.ServiceProvider] instance itself.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleans up the scope when exiting a context manager block.

        This calls the `dispose()` method to ensure all disposable services
        within the scope are properly cleaned up.

        Args:
            exc_type: The type of the exception that caused the context to be exited, if any.
            exc_val: The exception instance that caused the context to be exited, if any.
            exc_tb: A traceback object, if an exception occurred.
        """
        self.dispose()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _create_instance(self, desc: ServiceDescriptor[Any]) -> Any:
        """Creates an instance of a service based on its descriptor and applies decorators.

        This internal method handles the core logic of instantiation:
        1. If a factory is provided in the [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor], it's called.
        2. Otherwise, the `implementation_type` is instantiated, with its own
           dependencies resolved via constructor injection (see `_construct_via_type_hints`).
        3. Any registered decorators are applied in reverse order of registration
           (so the last registered decorator becomes the outermost wrapper).
           Circular decorator dependencies are checked during this phase.

        Args:
            desc: The [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] for the service to create.

        Returns:
            The fully constructed (and potentially decorated) service instance.

        Raises:
            [CircularDecoratorError][wd.di.exceptions.CircularDecoratorError]: If a cycle is detected during
                decorator application.
        """
        # Build inner service
        if desc.factory is not None:
            inner = desc.factory(self)
        else:  # constructor injection via type hints
            impl = desc.implementation_type
            assert impl is not None
            inner = self._construct_via_type_hints(impl)

        # Apply decorators (outermost == last registered)
        if desc.decorators:
            stack = _resolution_stack.get()
            for deco in reversed(desc.decorators):
                deco_frame = _key(deco)
                if deco_frame in stack:
                    cycle = stack[stack.index(deco_frame) :] + [deco_frame]
                    raise CircularDecoratorError(cycle)

                stack.append(deco_frame)
                _resolution_stack.set(stack)
                try:
                    inner = deco(self, inner)
                finally:
                    stack.pop()

        return inner

    # -- helper: constructor injection ---------------------------------- #
    def _construct_via_type_hints(self, cls: Type[Any]) -> Any:
        """Constructs an instance of `cls` by resolving its constructor dependencies.

        This method inspects the `__init__` method of the given class, resolves
        the type hints of its parameters by calling `get_service` for each, and
        then instantiates the class with these resolved dependencies.

        It handles classes with no explicit `__init__` or an `__init__` inherited
        directly from `object`.

        Type hints are resolved using `get_type_hints`, providing the class's
        module globals to help with forward references.

        Args:
            cls: The class type to instantiate.

        Returns:
            An instance of `cls`.

        Raises:
            TypeError: If a constructor parameter cannot be resolved or if there's
                an issue with type hint resolution (e.g., unresolvable forward reference
                not caught as a direct circular dependency by `get_service`).
            NameError: Potentially from `get_type_hints` if a forward reference
                cannot be resolved within the class's module context and isn't a
                service type itself (though `get_service` would usually catch this earlier).
        """
        # Get the constructor, __init__ might be inherited from object
        # For dataclasses or classes without explicit __init__, inspect.signature directly on class might be better
        # but __init__ is standard.
        constructor_to_inspect = cls.__init__
        if constructor_to_inspect is object.__init__ and not hasattr(cls, '__init__'): # Handle classes with no explicit __init__
             # If it's object.__init__ and there's no __init__ on the class itself (e.g. simple class Foo: pass)
             # then there are no parameters to inject.
             if not [p for p_name, p in inspect.signature(cls).parameters.items() if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]:
                 return cls()


        sig = inspect.signature(constructor_to_inspect)

        # Resolve type hints, providing globals and locals from the class's module
        # to help resolve forward references.
        try:
            # Get the module where the class `cls` is defined.
            module = inspect.getmodule(cls)
            if module is None:
                # Fallback if module cannot be determined (e.g. dynamically created classes)
                # This might limit forward reference resolution.
                resolved_hints = get_type_hints(constructor_to_inspect)
            else:
                resolved_hints = get_type_hints(constructor_to_inspect, module.__dict__)
        except NameError as e:
            # This is where the test expects the failure for unresolved forward reference in a cycle
            stack = _resolution_stack.get() # Get current resolution stack for error message
            # Ensure the current class being constructed is part of the reported stack if not already
            cls_key = _key(cls)
            if not stack or stack[-1] != cls_key: # Add if not already the last one
                effective_stack_for_error = stack + [cls_key]
            else:
                effective_stack_for_error = stack

            raise RuntimeError(
                f"Failed to resolve dependencies for {cls.__qualname__} "
                f"due to NameError (potential forward reference in a circular dependency): {e}. "
                f"Resolution stack: {effective_stack_for_error}"
            ) from e

        kwargs: Dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue

            actual_param_type = resolved_hints.get(name)

            if actual_param_type is None:
                # Parameter not in resolved_hints, could be *args, **kwargs, or missing annotation
                if param.kind == inspect.Parameter.VAR_POSITIONAL or \
                   param.kind == inspect.Parameter.VAR_KEYWORD:
                    continue # Skip *args, **kwargs
                raise TypeError(
                    f"Cannot resolve constructor parameter '{name}' for {cls.__qualname__}; "
                    f"missing type annotation or type could not be resolved."
                )

            kwargs[name] = self.get_service(actual_param_type)
        return cls(**kwargs)

    # -- helper: register disposables ----------------------------------- #
    def _try_register_disposable(self, instance: Any) -> None:
        """Registers an instance for disposal if it has a `dispose` or `close` method.

        This method checks if the provided `instance` has a callable `dispose`
        attribute or a callable `close` attribute. If so, the instance is added
        to the `_disposables` list for the current scope, ensuring it will be
        cleaned up when the scope is disposed.

        Args:
            instance: The service instance to check and potentially register.
        """
        if (hasattr(instance, "dispose") and callable(instance.dispose)) or (hasattr(instance, "close") and callable(instance.close)):
            self._disposables.append(instance)


# ---------------------------------------------------------------------- #
# Helper – make a readable stack entry name
# ---------------------------------------------------------------------- #

def _key(obj: object) -> str:
    """Generate a unique, human-readable key for an object (service type or decorator factory).

    This key is used for tracking objects in the `_resolution_stack` to detect
    circular dependencies.

    Args:
        obj: The object for which to generate a key.

    Returns:
        A string key. For types, it's `module.ClassName`. For callables, it attempts
        to use `__qualname__` or `__name__`. Falls back to `repr(obj)`.
    """
    if isinstance(obj, type):
        return obj.__qualname__
    if hasattr(obj, "__qualname__"):
        return obj.__qualname__  # type: ignore[attr-defined]
    if hasattr(obj, "__name__"):
        return obj.__name__  # type: ignore[attr-defined]
    return repr(obj)


# ---------------------------------------------------------------------- #
# Aliases – keep old import paths working
# ---------------------------------------------------------------------- #

Scope = ServiceProvider  # for back-compat
"""An alias for [ServiceProvider][wd.di.container.ServiceProvider], provided for backward compatibility.

In previous versions, `Scope` was a distinct subclass. Now, any [ServiceProvider][wd.di.container.ServiceProvider]
can act as a scope. This alias ensures that imports like
`from wd.di.container import Scope` continue to work.

A scope is typically created using `ServiceProvider.create_scope()` and is used
to manage the lifecycle of scoped services. It can be used as a context manager.
"""
