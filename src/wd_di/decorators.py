# di_container/decorators.py

from typing import Type

from . import services


def transient(service_type: Type = None):  # type: ignore
    def decorator(implementation_type: Type):
        services.add_transient(service_type or implementation_type, implementation_type)
        return implementation_type

    return decorator


def singleton(service_type: Type = None):  # type: ignore
    def decorator(implementation_type: Type):
        services.add_singleton(service_type or implementation_type, implementation_type)
        return implementation_type

    return decorator


def scoped(service_type: Type = None):  # type: ignore
    def decorator(implementation_type: Type):
        services.add_scoped(service_type or implementation_type, implementation_type)
        return implementation_type

    return decorator
