"""**wd-di**: A decorator-aware dependency injection library for Python.

This library provides a flexible and powerful dependency injection (DI) mechanism
for Python applications, inspired by systems like Microsoft.Extensions.DependencyInjection.

Key Features:
    - **Service Collection API**: Fluent API ([ServiceCollection][wd.di.service_collection.ServiceCollection]) for
      registering services, their implementations, and lifetimes.
    - **Service Lifetimes**: Supports transient, scoped, and singleton service lifetimes
      ([ServiceLifetime][wd.di.lifetimes.ServiceLifetime]).
    - **Decorator Support**: Allows decorating service instances to add cross-cutting
      concerns (e.g., logging, caching) without modifying the service code itself.
      See [ServiceCollection.decorate][wd.di.service_collection.ServiceCollection.decorate] and
      [DecoratorFactory][wd.di.descriptors.DecoratorFactory].
    - **Constructor Injection**: Services are instantiated by resolving their constructor
      dependencies from the container.
    - **Options Pattern**: Configuration binding to strongly-typed options objects
      ([Options][wd.di.config.Options], [IConfiguration][wd.di.config.IConfiguration]).
    - **Scopes**: Ability to create service scopes
      ([ServiceProvider.create_scope][wd.di.container.ServiceProvider.create_scope]) for managing
      scoped service instances.
    - **Middleware Pipeline**: Support for building and executing asynchronous
      middleware pipelines ([MiddlewarePipeline][wd.di.middleware.MiddlewarePipeline],
      [ApplicationBuilder][wd.di.middleware_di.ApplicationBuilder]).
    - **Custom Exceptions**: Clear error reporting through custom exceptions like
      [InvalidOperationError][wd.di.exceptions.InvalidOperationError] and
      [CircularDecoratorError][wd.di.exceptions.CircularDecoratorError].

Quick Start:
    ```python
    from wd.di import create_service_collection, ServiceLifetime

    # 1. Create a service collection
    services = create_service_collection()

    # 2. Register your services
    class IMyService:
        def do_work(self):
            pass

    class MyService(IMyService):
        def do_work(self):
            print("MyService is working!")

    services.add_transient(IMyService, MyService)

    # 3. Build the service provider
    provider = services.build_service_provider()

    # 4. Resolve and use services
    with provider.create_scope() as scope: # Scopes are good practice
        my_service_instance = scope.get_service(IMyService)
        my_service_instance.do_work()
    ```

This `__init__.py` file re-exports the main public symbols from the various
modules of the `wd.di` package for easier access.
"""
from importlib.metadata import PackageNotFoundError, version

from wd.di.config import IConfiguration, Options, OptionsBuilder
from wd.di.container import Scope, ServiceProvider
from wd.di.exceptions import CircularDecoratorError, InvalidOperationError
from wd.di.lifetimes import ServiceLifetime
from wd.di.middleware import (
    CachingMiddleware,
    ExceptionHandlerMiddleware,
    IMiddleware,
    LoggingMiddleware,
    MiddlewarePipeline,
    ValidationMiddleware,
)
from wd.di.middleware_di import create_application_builder
from wd.di.service_collection import ServiceCollection

__all__ = [
    "CachingMiddleware",
    "CircularDecoratorError",
    "ExceptionHandlerMiddleware",
    "IConfiguration",
    "IMiddleware",
    "InvalidOperationError",
    "LoggingMiddleware",
    "MiddlewarePipeline",
    "Options",
    "OptionsBuilder",
    "Scope",
    "ServiceCollection",
    "ServiceLifetime",
    "ServiceProvider",
    "ValidationMiddleware",
    "create_application_builder",
    "create_service_collection",
]

try:
    __version__ = version("wd-di")
except PackageNotFoundError:
    __version__ = "0.1.1"


# Attach extension methods
ServiceCollection.create_application_builder = create_application_builder

def create_service_collection() -> ServiceCollection:
    """Creates and returns a new, empty [ServiceCollection][wd.di.service_collection.ServiceCollection].

    This is a convenience factory function to easily obtain a new service
    collection instance to begin registering services.

    Returns:
        A new [ServiceCollection][wd.di.service_collection.ServiceCollection] instance.
    """
    return ServiceCollection()
