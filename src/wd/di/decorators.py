from typing import TypeVar, Type, Optional, Callable, cast, overload

from . import services

T = TypeVar('T')
S = TypeVar('S')

@overload
def transient() -> Callable[[Type[T]], Type[T]]: ...

@overload
def transient(service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

def transient(service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:
    def decorator(implementation_type: Type[T]) -> Type[T]:
        if service_type is None:
            # When no interface is provided, register the implementation type as both service and implementation
            services.add_transient(implementation_type, implementation_type)
        else:
            services.add_transient(service_type, implementation_type)
        return implementation_type
    return decorator

@overload
def singleton() -> Callable[[Type[T]], Type[T]]: ...

@overload
def singleton(service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

def singleton(service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:
    def decorator(implementation_type: Type[T]) -> Type[T]:
        if service_type is None:
            # When no interface is provided, register the implementation type as both service and implementation
            services.add_singleton(implementation_type, implementation_type)
        else:
            services.add_singleton(service_type, implementation_type)
        return implementation_type
    return decorator

@overload
def scoped() -> Callable[[Type[T]], Type[T]]: ...

@overload
def scoped(service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

def scoped(service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:
    def decorator(implementation_type: Type[T]) -> Type[T]:
        if service_type is None:
            # When no interface is provided, register the implementation type as both service and implementation
            services.add_scoped(implementation_type, implementation_type)
        else:
            services.add_scoped(service_type, implementation_type)
        return implementation_type
    return decorator
