from importlib.metadata import PackageNotFoundError, version


from wd.di.service_collection import ServiceCollection
from wd.di.container import ServiceProvider, Scope
from wd.di.exceptions import InvalidOperationError, CircularDecoratorError
from wd.di.lifetimes import ServiceLifetime
from wd.di.config import IConfiguration, Options, OptionsBuilder

from wd.di.middleware import (
    IMiddleware,
    MiddlewarePipeline,
    LoggingMiddleware,
    ValidationMiddleware,
    CachingMiddleware,
    ExceptionHandlerMiddleware,
)
from wd.di.middleware_di import create_application_builder

__all__ = [
    "ServiceCollection",
    "create_service_collection",
    "ServiceProvider",
    "Scope",
    "InvalidOperationError",
    "CircularDecoratorError",
    "ServiceLifetime",
    "IConfiguration",
    "Options",
    "OptionsBuilder",
    "IMiddleware",
    "MiddlewarePipeline",
    "LoggingMiddleware",
    "ValidationMiddleware",
    "CachingMiddleware",
    "ExceptionHandlerMiddleware",
    "create_application_builder",
]

try:
    __version__ = version("wd-di")
except PackageNotFoundError:
    __version__ = "0.1.1"


# Attach extension methods
ServiceCollection.create_application_builder = create_application_builder

def create_service_collection() -> ServiceCollection:
    """Return a brand-new, empty service collection."""
    return ServiceCollection()
