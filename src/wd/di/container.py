"""Runtime *service provider* for **wd-di** (decorator-aware, backward-compatible).

This module keeps 100% API compatibility with the pre-decorator version while
adding

* first-class **decorator folding** (see :pyclass:`ServiceDescriptor`) and
* task-local **circular-decorator detection**.

Back-compat shims
-----------------
* ``ServiceProvider.__init__`` now accepts **either** the historical
  ``Dict[Type, ServiceDescriptor]`` **or** a ``List[ServiceDescriptor]`` (the
  format emitted by the new :pyclass:`~wd.di.service_collection.ServiceCollection`).
* A lightweight :pyclass:`Scope` alias mirrors the previous subclass so import
  paths like ``from wd.di.container import Scope`` keep working.  A scoped
  provider supports ``dispose()``, ``close()`` semantics and can be used as a
  context manager (``with services.create_scope() as scope: ...``).
"""

from __future__ import annotations

import contextvars
import inspect
import threading
from typing import Any, Dict, List, Mapping, Sequence, Type, TypeVar, Union, overload, get_type_hints

from .descriptors import ServiceDescriptor
from .exceptions import CircularDecoratorError, InvalidOperationError
from .lifetimes import ServiceLifetime

__all__ = ["ServiceProvider", "Scope"]

T = TypeVar("T")

# --------------------------------------------------------------------------- #
# Task-local resolution stack (dependency & decorator cycles)
# --------------------------------------------------------------------------- #

_resolution_stack: contextvars.ContextVar[List[str]] = contextvars.ContextVar(
    "wd_di_resolution_stack", default=[]
)


class ServiceProvider:  # noqa: D101 – public runtime DI container
    # NOTE: 'services' can be a mapping (old API) **or** a list (new API)
    def __init__(
        self,
        services: Union[Sequence[ServiceDescriptor[Any]], Mapping[Type[Any], ServiceDescriptor[Any]]],
        *,
        _root: "ServiceProvider | None" = None,
    ) -> None:
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
        """Resolve *service_type*, creating & caching it as needed."""
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
        """Return a *scoped* provider that shares singletons with the root."""
        return ServiceProvider([], _root=self._root)

    # ------------------------------------------------------------------ #
    # Disposal (scoped provider)
    # ------------------------------------------------------------------ #
    def dispose(self):  # noqa: D401 – verb form mirrors old API
        """Dispose all tracked scoped instances (close / dispose)."""
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
    def __enter__(self):  # noqa: D401 – magic method
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: D401 – magic method
        self.dispose()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _create_instance(self, desc: ServiceDescriptor[Any]) -> Any:
        """Instantiate *desc* and apply registered decorators."""
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
        if hasattr(instance, "dispose") and callable(instance.dispose):
            self._disposables.append(instance)
        elif hasattr(instance, "close") and callable(instance.close):
            self._disposables.append(instance)


# ---------------------------------------------------------------------- #
# Helper – make a readable stack entry name
# ---------------------------------------------------------------------- #

def _key(obj: object) -> str:
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

Scope = ServiceProvider  # backward-compat
