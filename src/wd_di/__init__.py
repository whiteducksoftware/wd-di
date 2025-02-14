from .service_collection import ServiceCollection
from .middleware import (
    IMiddleware,
    MiddlewarePipeline,
    LoggingMiddleware,
    ValidationMiddleware,
    CachingMiddleware,
    ExceptionHandlerMiddleware,
)
from .middleware_di import create_application_builder

__version__ = "0.1.0"
services = ServiceCollection()

# Attach extension methods
ServiceCollection.create_application_builder = create_application_builder
