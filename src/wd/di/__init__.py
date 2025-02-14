from importlib.metadata import PackageNotFoundError, version


from wd.di.service_collection import ServiceCollection
from wd.di.middleware import (
    IMiddleware,
    MiddlewarePipeline,
    LoggingMiddleware,
    ValidationMiddleware,
    CachingMiddleware,
    ExceptionHandlerMiddleware,
)
from wd.di.middleware_di import create_application_builder

try:
    __version__ = version("wd-di")
except PackageNotFoundError:
    __version__ = "0.1.1"


services = ServiceCollection()

# Attach extension methods
ServiceCollection.create_application_builder = create_application_builder
