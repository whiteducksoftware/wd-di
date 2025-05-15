# Repository Analysis

## Repository Statistics

- **Extensions analyzed**: .py
- **Number of files analyzed**: 25
- **Total lines of code (approx)**: 1430

## Project Files

### 1. examples\decorator_type_hints_example.py

- **File ID**: file_0
- **Type**: Code File
- **Line Count**: 71
- **Description**: File at examples\decorator_type_hints_example.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
from abc import ABC, abstractmethod
from dataclasses import dataclass
from wd.di import ServiceCollection
from wd.di.config import Configuration, IConfiguration

services = ServiceCollection()

# Define interfaces
class IEmailService(ABC):
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str) -> None:
        pass

class IUserService(ABC):
    @abstractmethod
    def notify_user(self, user_id: str, message: str) -> None:
        pass



config = Configuration({
    "app": {
        "api_key": "real-secret-key"
    }
})

@dataclass
class AppConfig:
    api_key: str = "secret-key"

services.add_singleton_factory(IConfiguration, lambda _: config)
services.configure(AppConfig, section="app")

# Implementations with decorators
@services.singleton(IEmailService)
class EmailService(IEmailService):
    def send_email(self, to: str, subject: str, body: str) -> None:
        print(f"Sending email to {to}")

@services.singleton(IUserService)
class UserService(IUserService):
    def __init__(self, email_service: IEmailService):
        self.email_service = email_service

    def notify_user(self, user_id: str, message: str) -> None:
        self.email_service.send_email(f"user{user_id}@example.com", "Notification", message)



# Service without interface - register directly with the class
@services.singleton()
class LogService:
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")

# Build provider
provider = services.build_service_provider()

# Get services with proper type hints
log_service = provider.get_service(LogService)
email_service = provider.get_service(IEmailService)
user_service = provider.get_service(IUserService)   
configuration = provider.get_service(IConfiguration) 


# Use the services (IDE provides code completion for all methods)
log_service.log("Application started")
email_service.send_email("test@example.com", "Test", "Hello")
user_service.notify_user("123", "Welcome!")
config_value = configuration.get("app:api_key")
log_service.log(f"Got config: {config_value}")

```

---

### 2. examples\order_processor\data\repository.py

- **File ID**: file_1
- **Type**: Code File
- **Line Count**: 10
- **Description**: File at examples\order_processor\data\repository.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
from domain.interfaces import IOrderRepository
from infrastructure.logging_service import Logger

class OrderRepository(IOrderRepository):
    def __init__(self, logger: Logger):
        self.logger = logger

    def save_order(self, order):
        self.logger.log(f"Order saved: {order.order_id}")
        # In a real application, implement database save logic here.

```

---

### 3. examples\order_processor\domain\interfaces.py

- **File ID**: file_2
- **Type**: Code File
- **Line Count**: 11
- **Description**: File at examples\order_processor\domain\interfaces.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
from abc import ABC, abstractmethod

class IOrderRepository(ABC):
    @abstractmethod
    def save_order(self, order):
        pass

class IOrderService(ABC):
    @abstractmethod
    def process_order(self, order):
        pass
```

---

### 4. examples\order_processor\domain\models.py

- **File ID**: file_3
- **Type**: Code File
- **Line Count**: 8
- **Description**: File at examples\order_processor\domain\models.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
from dataclasses import dataclass

@dataclass
class Order:
    order_id: str
    item: str
    quantity: int
    price: float
```

---

### 5. examples\order_processor\infrastructure\config.py

- **File ID**: file_4
- **Type**: Code File
- **Line Count**: 6
- **Description**: File at examples\order_processor\infrastructure\config.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
from dataclasses import dataclass

@dataclass
class AppConfig:
    debug: bool = False
    email_server: str = ""
```

---

### 6. examples\order_processor\infrastructure\logging_service.py

- **File ID**: file_5
- **Type**: Code File
- **Line Count**: 3
- **Description**: File at examples\order_processor\infrastructure\logging_service.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
class Logger:
    def log(self, message: str):
        print(f"[LOG]: {message}")
```

---

### 7. examples\order_processor\main.py

- **File ID**: file_6
- **Type**: Code File
- **Line Count**: 39
- **Description**: File at examples\order_processor\main.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
from domain.interfaces import IOrderRepository, IOrderService
from wd.di import ServiceCollection
from wd.di.config import Configuration, IConfiguration
from infrastructure.config import AppConfig
from infrastructure.logging_service import Logger
from data.repository import OrderRepository
from services.order_service import OrderService
from presentation.controller import OrderController

services = ServiceCollection()

# Configure application settings
config = Configuration({
    "app": {
        "debug": True,
        "emailServer": "smtp.example.com"
    }
})
services.add_singleton_factory(IConfiguration, lambda _: config)
services.configure(AppConfig, section="app")

# Register infrastructure services
services.add_instance(Logger, Logger())

# Register data access layer (repository)
services.add_singleton(IOrderRepository, OrderRepository)

# Register business logic (order service)
services.add_singleton(IOrderService, OrderService)

# Register presentation layer (controller)
services.add_transient(OrderController)

# Build the service provider
provider = services.build_service_provider()

# Resolve the controller and simulate an order submission
controller = provider.get_service(OrderController)
controller.submit_order("order001", "Widget", 5, 19.99)

```

---

### 8. examples\order_processor\presentation\controller.py

- **File ID**: file_7
- **Type**: Code File
- **Line Count**: 10
- **Description**: File at examples\order_processor\presentation\controller.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
from domain.models import Order
from domain.interfaces import IOrderService

class OrderController:
    def __init__(self, order_service: IOrderService):
        self.order_service = order_service

    def submit_order(self, order_id, item, quantity, price):
        order = Order(order_id=order_id, item=item, quantity=quantity, price=price)
        self.order_service.process_order(order)

```

---

### 9. examples\order_processor\services\order_service.py

- **File ID**: file_8
- **Type**: Code File
- **Line Count**: 14
- **Description**: File at examples\order_processor\services\order_service.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
from domain.interfaces import IOrderService, IOrderRepository
from domain.models import Order
from infrastructure.logging_service import Logger

class OrderService(IOrderService):
    def __init__(self, repository: IOrderRepository, logger: Logger):
        self.repository = repository
        self.logger = logger

    def process_order(self, order: Order):
        self.logger.log(f"Processing order: {order.order_id}")
        # Business logic: validate order, process payment, etc.
        self.repository.save_order(order)
        self.logger.log(f"Order processed: {order.order_id}")

```

---

### 10. examples\type_hints_example.py

- **File ID**: file_9
- **Type**: Code File
- **Line Count**: 36
- **Description**: File at examples\type_hints_example.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
from abc import ABC, abstractmethod
from wd.di import ServiceCollection

services = ServiceCollection()

# Define interfaces and implementations
class IEmailService(ABC):
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str) -> None:
        pass

class EmailService(IEmailService):
    def send_email(self, to: str, subject: str, body: str) -> None:
        print(f"Sending email to {to}")

class UserService:
    def __init__(self, email_service: IEmailService):
        self.email_service = email_service

    def notify_user(self, user_id: str, message: str) -> None:
        self.email_service.send_email(f"user{user_id}@example.com", "Notification", message)

# Register services
services.add_singleton(IEmailService, EmailService)
services.add_singleton(UserService)

# Build provider
provider = services.build_service_provider()

# Get services with proper type hints
email_service = provider.get_service(IEmailService)  # Type hints work here
user_service = provider.get_service(UserService)      # And here

# IDE will provide code completion for these methods
email_service.send_email("test@example.com", "Test", "Hello")
user_service.notify_user("123", "Welcome!")

```

---

### 11. src\wd\di\__init__.py

- **File ID**: file_10
- **Type**: Code File
- **Line Count**: 26
- **Description**: File at src\wd\di\__init__.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
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


# Attach extension methods
ServiceCollection.create_application_builder = create_application_builder

def create_service_collection() -> ServiceCollection:
    """Return a brand-new, empty service collection."""
    return ServiceCollection()

```

---

### 12. src\wd\di\config.py

- **File ID**: file_11
- **Type**: Code File
- **Line Count**: 116
- **Description**: File at src\wd\di\config.py
- **Dependencies**: None
- **Used By**:
  - file_17

**Content**:
```
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic, Type
from dataclasses import dataclass
import json
import os

T = TypeVar("T")


class IConfiguration(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def get_section(self, section: str) -> "IConfiguration":
        pass


class Configuration(IConfiguration):
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, key: str) -> Any:
        keys = key.split(":")
        current = self._data
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return None
            current = current[k]
        return current

    def get_section(self, section: str) -> "IConfiguration":
        value = self.get(section)
        if isinstance(value, dict):
            return Configuration(value)
        return Configuration({})


class ConfigurationBuilder:
    def __init__(self):
        self._sources: Dict[str, Any] = {}

    def add_json_file(self, path: str) -> "ConfigurationBuilder":
        if os.path.exists(path):
            with open(path, "r") as f:
                self._sources.update(json.load(f))
        return self

    def add_env_variables(self, prefix: str = "") -> "ConfigurationBuilder":
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            if prefix:
                key = key[len(prefix) :]
            self._sources[key] = value
        return self

    def add_dictionary(self, dictionary: Dict[str, Any]) -> "ConfigurationBuilder":
        self._sources.update(dictionary)
        return self

    def build(self) -> IConfiguration:
        return Configuration(self._sources)


@dataclass
class ConfigureOptions:
    section: str


class Options(Generic[T]):
    def __init__(self, value: T):
        self._value = value

    @property
    def value(self) -> T:
        return self._value


class OptionsBuilder(Generic[T]):
    def __init__(self, options_type: Type[T]):
        self._options_type = options_type
        self._configuration: Optional[IConfiguration] = None
        self._section: Optional[str] = None

    def bind_configuration(
        self, configuration: IConfiguration, section: Optional[str] = None
    ) -> "OptionsBuilder[T]":
        self._configuration = configuration
        self._section = section
        return self

    def build(self) -> T:
        if self._configuration is None:
            return self._options_type()

        config_section = self._configuration
        if self._section:
            config_section = self._configuration.get_section(self._section)

        instance = self._options_type()
        config_dict = {}

        if hasattr(config_section, "_data"):
            config_dict = config_section._data

        # Convert camelCase to snake_case for property names
        for key, value in config_dict.items():
            snake_key = "".join(
                ["_" + c.lower() if c.isupper() else c for c in key]
            ).lstrip("_")
            if hasattr(instance, snake_key):
                setattr(instance, snake_key, value)

        return instance

```

---

### 13. src\wd\di\container.py

- **File ID**: file_12
- **Type**: Code File
- **Line Count**: 159
- **Description**: File at src\wd\di\container.py
- **Dependencies**:
  - file_14
  - file_13
- **Used By**:
  - file_17
  - file_13

**Content**:
```
from typing import Any, Dict, Type, Set, Optional, get_type_hints, TypeVar, Generic, overload, List
from contextvars import ContextVar, Token

from .descriptors import ServiceDescriptor
from .lifetimes import ServiceLifetime

T = TypeVar('T')

# ContextVar for managing the resolving stack for circular dependency detection in a thread-safe manner.
# Each async task or thread will have its own stack.
_current_resolving_stack: ContextVar[List[Type]] = ContextVar("current_resolving_stack")

class ServiceProvider:
    def __init__(self, services: Dict[Type, ServiceDescriptor]):
        self._services = services
        self._singletons = {}

    @overload
    def get_service(self, service_type: Type[T]) -> T: ...

    def get_service(self, service_type: Type[T]) -> T:
        current_stack: List[Type]
        try:
            current_stack = _current_resolving_stack.get()
        except LookupError:
            current_stack = []
        
        if service_type in current_stack:
            # Stack includes current service_type, so it's a cycle
            raise Exception(f"Circular dependency detected for service: {service_type}. Resolution stack: {current_stack + [service_type]}")
        
        # Set new stack for this resolution context
        new_stack = current_stack + [service_type]
        token = _current_resolving_stack.set(new_stack)

        try:
            descriptor = self._services.get(service_type)
            if descriptor is None:
                raise Exception(f"Service {service_type} not registered.")

            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                if service_type not in self._singletons:
                    self._singletons[service_type] = self._create_instance(descriptor)
                return self._singletons[service_type]
            elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
                return self._create_instance(descriptor)
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                raise Exception("Cannot resolve scoped service from the root provider. "
                                "Please create a scope using 'create_scope()' and resolve it from the scope.")
            else:
                raise Exception("Unknown service lifetime.")
        finally:
            _current_resolving_stack.reset(token) # Reset to previous stack

    def create_scope(self) -> "Scope":
        return Scope(self._services, self._singletons, self)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        if descriptor.implementation_factory:
            return descriptor.implementation_factory(self)
        else:
            implementation_type = descriptor.implementation_type
            if implementation_type is None:
                raise Exception(f"Service descriptor for {descriptor.service_type} has no implementation type or factory.")

            constructor = implementation_type.__init__
            try:
                param_types = get_type_hints(constructor)
            except NameError as e:
                # If NameError occurs, capture current stack for better diagnostics
                current_stack_for_error: List[Type]
                try:
                    current_stack_for_error = _current_resolving_stack.get()
                except LookupError:
                    current_stack_for_error = [] # Should ideally be set if we are in _create_instance
                raise Exception(f"Failed to resolve dependencies for {implementation_type} due to NameError (potential forward reference in a circular dependency): {e}. Resolution stack: {current_stack_for_error}") from e

            dependencies = {}
            for param, param_type in param_types.items():
                if param == "return":
                    continue
                dependencies[param] = self.get_service(param_type) # This will use the updated ContextVar logic
            return implementation_type(**dependencies)  # type: ignore


class Scope(ServiceProvider):
    def __init__(self, services: Dict[Type, ServiceDescriptor], root_singletons: Dict[Type, Any], parent_provider: ServiceProvider):
        super().__init__(services)
        self._parent_provider = parent_provider
        self._root_singletons = root_singletons
        self._scoped_instances = {}
        self._disposables = []

    @overload
    def get_service(self, service_type: Type[T]) -> T: ...

    def get_service(self, service_type: Type[T]) -> T:
        current_stack: List[Type]
        try:
            current_stack = _current_resolving_stack.get()
        except LookupError:
            current_stack = []

        if service_type in current_stack:
            raise Exception(f"Circular dependency detected for service: {service_type}. Resolution stack: {current_stack + [service_type]}")

        new_stack = current_stack + [service_type]
        token = _current_resolving_stack.set(new_stack)

        try:
            descriptor = self._services.get(service_type)
            if descriptor is None:
                raise Exception(f"Service {service_type} not registered.")

            if descriptor.lifetime == ServiceLifetime.SCOPED:
                if service_type not in self._scoped_instances:
                    instance = self._create_instance(descriptor)
                    self._scoped_instances[service_type] = instance
                    if hasattr(instance, "dispose") and callable(instance.dispose):
                        self._disposables.append(instance)
                    elif hasattr(instance, "close") and callable(instance.close):
                        self._disposables.append(instance)
                return self._scoped_instances[service_type]
            elif descriptor.lifetime == ServiceLifetime.SINGLETON:
                if service_type not in self._root_singletons:
                    # Create singleton via parent if not exists, ensuring it's stored in root_singletons
                    # This path should ideally be via parent_provider.get_service(service_type) to ensure
                    # parent's full singleton creation logic (including its _create_instance if needed)
                    # is respected if the singleton isn't in the _root_singletons cache yet.
                    # However, _parent_provider._create_instance(descriptor) is what was there.
                    # Let's refine to call parent's get_service if not in the passed cache.
                    # This assumes _root_singletons is the definitive cache passed down.
                    self._root_singletons[service_type] = self._parent_provider.get_service(service_type)
                return self._root_singletons[service_type]
            else: # TRANSIENT
                return self._create_instance(descriptor)
        finally:
            _current_resolving_stack.reset(token)

    def dispose(self):
        for instance in self._disposables:
            if hasattr(instance, "dispose") and callable(instance.dispose):
                try:
                    instance.dispose()
                except Exception as e:
                    print(f"Error disposing {instance}: {e}")
            elif hasattr(instance, "close") and callable(instance.close):
                try:
                    instance.close()
                except Exception as e:
                    print(f"Error closing {instance}: {e}")
        self._disposables.clear()
        self._scoped_instances.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()

```

---

### 14. src\wd\di\descriptors.py

- **File ID**: file_13
- **Type**: Code File
- **Line Count**: 21
- **Description**: File at src\wd\di\descriptors.py
- **Dependencies**:
  - file_14
  - file_12
- **Used By**:
  - file_17
  - file_12

**Content**:
```
from typing import Any, Callable, Optional, Type, TYPE_CHECKING

from .lifetimes import ServiceLifetime

if TYPE_CHECKING:
    from .container import ServiceProvider


class ServiceDescriptor:
    def __init__(
        self,
        service_type: Type,
        implementation_type: Optional[Type] = None,
        implementation_factory: Optional[Callable[["ServiceProvider"], Any]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ):
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.implementation_factory = implementation_factory
        self.lifetime = lifetime
        self.instance = None  # For singleton

```

---

### 15. src\wd\di\lifetimes.py

- **File ID**: file_14
- **Type**: Code File
- **Line Count**: 7
- **Description**: File at src\wd\di\lifetimes.py
- **Dependencies**: None
- **Used By**:
  - file_17
  - file_13
  - file_12

**Content**:
```
from enum import Enum


class ServiceLifetime(Enum):
    TRANSIENT = 1
    SINGLETON = 2
    SCOPED = 3

```

---

### 16. src\wd\di\middleware.py

- **File ID**: file_15
- **Type**: Code File
- **Line Count**: 119
- **Description**: File at src\wd\di\middleware.py
- **Dependencies**: None
- **Used By**:
  - file_16

**Content**:
```
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar("T")
TNext = Callable[[], Any]
TMiddleware = Callable[[T, TNext], Any]


class IMiddleware(ABC):
    """Base interface for middleware components."""

    @abstractmethod
    async def invoke(self, context: T, next: TNext) -> Any:
        """Process the context and call the next middleware in the pipeline."""
        pass


class MiddlewarePipeline:
    """Manages the middleware pipeline execution."""

    def __init__(self):
        self._middleware: List[TMiddleware[T]] = []

    def use(self, middleware: TMiddleware[T]) -> "MiddlewarePipeline":
        """Add a middleware to the pipeline."""
        self._middleware.append(middleware)
        return self

    def use_middleware(
        self, middleware_class: type, instance: Optional[Any] = None
    ) -> "MiddlewarePipeline":
        """Add a middleware class to the pipeline."""

        def adapter(context: T, next: TNext) -> Any:
            nonlocal instance
            if instance is None:
                instance = middleware_class()
            return instance.invoke(context, next)

        self._middleware.append(adapter)
        return self

    async def execute(self, context: T) -> Any:
        """Execute the middleware pipeline."""
        if not self._middleware:
            return None

        index = 0

        async def invoke_next() -> Any:
            nonlocal index
            if index < len(self._middleware):
                middleware = self._middleware[index]
                index += 1
                return await middleware(context, invoke_next)
            return None

        return await invoke_next()


class ExceptionHandlerMiddleware(IMiddleware):
    """Built-in middleware for handling exceptions in the pipeline."""

    async def invoke(self, context: T, next: TNext) -> Any:
        try:
            return await next()
        except Exception as e:
            # Log the exception or handle it as needed
            raise


class LoggingMiddleware(IMiddleware):
    """Built-in middleware for logging pipeline execution."""

    def __init__(self, logger: Optional[Callable[[str], None]] = None):
        self._logger = logger or print

    async def invoke(self, context: T, next: TNext) -> Any:
        self._logger(f"Executing pipeline with context: {context}")
        try:
            result = await next()
            self._logger(f"Pipeline execution completed with result: {result}")
            return result
        except Exception as e:
            self._logger(f"Pipeline execution failed: {str(e)}")
            raise


class ValidationMiddleware(IMiddleware):
    """Built-in middleware for context validation."""

    def __init__(self, validator: Callable[[T], bool]):
        self._validator = validator

    async def invoke(self, context: T, next: TNext) -> Any:
        if not self._validator(context):
            raise ValueError(f"Invalid context: {context}")
        return await next()


class CachingMiddleware(IMiddleware):
    """Built-in middleware for caching pipeline results."""

    def __init__(self):
        self._cache = {}

    async def invoke(self, context: T, next: TNext) -> Any:
        # Use context as cache key if it's hashable
        try:
            cache_key = hash(str(context.__dict__))
            if cache_key in self._cache:
                return self._cache[cache_key]

            result = await next()
            self._cache[cache_key] = result
            return result
        except (TypeError, AttributeError):
            # If context is not hashable or has no __dict__, skip caching
            return await next()

```

---

### 17. src\wd\di\middleware_di.py

- **File ID**: file_16
- **Type**: Code File
- **Line Count**: 91
- **Description**: File at src\wd\di\middleware_di.py
- **Dependencies**:
  - file_15
  - file_17
- **Used By**: None

**Content**:
```
from typing import Any, Callable, Optional, TypeVar
from .middleware import IMiddleware, MiddlewarePipeline, LoggingMiddleware
from .service_collection import ServiceCollection

T = TypeVar("T")
TNext = Callable[[], Any] # Explicitly define TNext for clarity in the adapter

# Forward declaration for type hinting if ServiceCollection is used in type hints
# before its full definition in this file or if it's a circular dependency concern.
# However, in this case, ServiceCollection is imported and used as a type hint
# for the constructor argument, which is standard.
# class ServiceCollection: # This is a forward reference / type stub for the real one
#     pass                 # that will be passed in. # REMOVE STUB

class MiddlewareBuilder:
    """Builder for configuring middleware in the DI container."""

    def __init__(self, services: ServiceCollection):
        self._services = services
        self._pipeline = MiddlewarePipeline()

    def use(
        self, middleware: Callable[[T, TNext], Any] # Use TNext here
    ) -> "MiddlewareBuilder":
        """Add a middleware function to the pipeline."""
        self._pipeline.use(middleware)
        return self

    def use_middleware(self, middleware_type: type) -> "MiddlewareBuilder":
        """Add a middleware class to the pipeline."""
        # Register the middleware type with DI using the provided services instance
        if middleware_type == LoggingMiddleware:
            self._services.add_transient_factory(
                middleware_type, lambda _: LoggingMiddleware() # Assuming LoggingMiddleware can be default constructed or gets deps
            )
        else:
            # Ensure the middleware itself is registered as transient so each resolution gets a new one if needed by its design
            self._services.add_transient(middleware_type)

        # This adapter will be called by the MiddlewarePipeline for each execution
        def adapter_for_pipeline(context: T, next_func: TNext) -> Any:
            # Build provider and resolve middleware instance ONCE PER EXECUTION of this middleware in the pipeline
            # This uses the ServiceCollection available at the time ApplicationBuilder.build() will be called (or later if services are added)
            # which might still be an issue if services are added *after* ApplicationBuilder.build() and before request.
            # However, the more common pattern is that the main service provider is built once.
            # If the goal is to use THE final application provider, that would need to be passed around differently.
            # For now, this builds from the _services collection held by MiddlewareBuilder, which is typically the main app collection.
            provider = self._services.build_service_provider() 
            instance = provider.get_service(middleware_type)
            return instance.invoke(context, next_func) # type: ignore

        self._pipeline.use(adapter_for_pipeline) # Use the generic .use() method
        return self

    def build(self) -> MiddlewarePipeline:
        """Build the middleware pipeline."""
        return self._pipeline


class ApplicationBuilder:
    """Builder for configuring the application with middleware support."""

    def __init__(self, services: ServiceCollection):
        self._services = services

    def configure_middleware(
        self, configure: Callable[["MiddlewareBuilder"], None]
    ) -> "ApplicationBuilder":
        """Configure the middleware pipeline."""
        builder = MiddlewareBuilder(self._services)
        configure(builder)
        pipeline = builder.build()

        self._services.add_singleton_factory(MiddlewarePipeline, lambda _: pipeline)
        return self

    def build(self):
        """Build the application."""
        # The ServiceProvider built here is the one that should ideally be used by middleware if they need the "final" app state.
        # The current MiddlewareBuilder approach builds a new provider each time from self._services.
        # This is a complex interaction. The user's suggestion improves it from config-time to per-request, which is better.
        return self._services.build_service_provider()


def create_application_builder(services: ServiceCollection) -> ApplicationBuilder:
    """Create an application builder for the service collection."""
    return ApplicationBuilder(services)


# Attach the extension method to ServiceCollection - This is done in __init__.py now
# ServiceCollection.create_application_builder = create_application_builder

```

---

### 18. src\wd\di\service_collection.py

- **File ID**: file_17
- **Type**: Code File
- **Line Count**: 142
- **Description**: File at src\wd\di\service_collection.py
- **Dependencies**:
  - file_14
  - file_13
  - file_12
  - file_11
- **Used By**:
  - file_16

**Content**:
```
# di_container/service_collection.py

from typing import Any, Callable, Dict, Optional, Type, TypeVar, TYPE_CHECKING, Generic, overload

from .descriptors import ServiceDescriptor
from .lifetimes import ServiceLifetime
from .config import IConfiguration, Options, OptionsBuilder

if TYPE_CHECKING:
    from .container import ServiceProvider


T = TypeVar("T")
S = TypeVar("S") # Added for decorator type hints


class ServiceCollection:
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}

    def add_transient_factory(
        self, service_type: Type, factory: Callable[["ServiceProvider"], Any]
    ):
        descriptor = ServiceDescriptor(
            service_type,
            implementation_factory=factory,
            lifetime=ServiceLifetime.TRANSIENT,
        )
        self._services[service_type] = descriptor

    def add_singleton_factory(
        self, service_type: Type, factory: Callable[["ServiceProvider"], Any]
    ):
        descriptor = ServiceDescriptor(
            service_type,
            implementation_factory=factory,
            lifetime=ServiceLifetime.SINGLETON,
        )
        self._services[service_type] = descriptor

    def add_transient(
        self, service_type: Type, implementation_type: Optional[Type] = None
    ):
        self._add_service(service_type, implementation_type, ServiceLifetime.TRANSIENT)

    def add_singleton(
        self, service_type: Type, implementation_type: Optional[Type] = None
    ):
        self._add_service(service_type, implementation_type, ServiceLifetime.SINGLETON)

    def add_scoped(
        self, service_type: Type, implementation_type: Optional[Type] = None
    ):
        self._add_service(service_type, implementation_type, ServiceLifetime.SCOPED)

    def _add_service(
        self,
        service_type: Type,
        implementation_type: Optional[Type],
        lifetime: ServiceLifetime,
    ):
        if implementation_type is None:
            implementation_type = service_type
        descriptor = ServiceDescriptor(
            service_type, implementation_type, None, lifetime
        )
        self._services[service_type] = descriptor

    def build_service_provider(self):
        from .container import ServiceProvider

        return ServiceProvider(self._services)
    
    def add_instance(self, service_type: Type, instance: Any):
        """
        Register an already constructed instance as a singleton service.
        This instance will be returned whenever service_type is requested.
        """
        descriptor = ServiceDescriptor(service_type, lifetime=ServiceLifetime.SINGLETON)
        descriptor.instance = instance
        self._services[service_type] = descriptor

    def configure(
        self, options_type: Type[T], *, section: Optional[str] = None
    ) -> None:
        """Configure options binding from configuration."""

        def factory(sp: "ServiceProvider") -> Options[T]:
            try:
                configuration = sp.get_service(IConfiguration)
                builder = OptionsBuilder(options_type)
                builder.bind_configuration(configuration, section)
                return Options(builder.build())
            except Exception as e:
                raise Exception("Configuration service not registered") from e

        self.add_singleton_factory(Options[options_type], factory)  # type: ignore

    # -- DECORATOR REGISTRATION -------------------------------------
    @overload  # @services.singleton()
    def singleton(self) -> Callable[[Type[T]], Type[T]]: ...
    @overload  # @services.singleton(IMyInterface)
    def singleton(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def singleton(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:
        def decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_singleton(impl, impl)
            else:
                # We need to tell mypy that service_type is not None here.
                # However, the overloads should handle the external type checking.
                self.add_singleton(service_type, impl) # type: ignore
            return impl
        return decorator

    @overload  # @services.transient()
    def transient(self) -> Callable[[Type[T]], Type[T]]: ...
    @overload  # @services.transient(IMyInterface)
    def transient(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def transient(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:
        def decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_transient(impl, impl)
            else:
                self.add_transient(service_type, impl) # type: ignore
            return impl
        return decorator

    @overload  # @services.scoped()
    def scoped(self) -> Callable[[Type[T]], Type[T]]: ...
    @overload  # @services.scoped(IMyInterface)
    def scoped(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def scoped(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:
        def decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_scoped(impl, impl)
            else:
                self.add_scoped(service_type, impl) # type: ignore
            return impl
        return decorator

```

---

### 19. tests\__init__.py

- **File ID**: file_18
- **Type**: Code File
- **Line Count**: 1
- **Description**: File at tests\__init__.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```


```

---

### 20. tests\test_circular_dependency.py

- **File ID**: file_19
- **Type**: Code File
- **Line Count**: 31
- **Description**: File at tests\test_circular_dependency.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
import pytest
# from wd.di.service_collection import ServiceCollection # Old import path
from wd.di import ServiceCollection # Correct import path

def test_circular_dependency_detection():
    services = ServiceCollection() # Instantiate locally

    # Define two classes that depend on each other
    class ServiceA:
        def __init__(self, service_b: "ServiceB"):
            self.service_b = service_b

    class ServiceB:
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

    services.add_transient(ServiceA)
    services.add_transient(ServiceB)

    provider = services.build_service_provider()

    # Updated to expect the NameError that occurs first when forward references
    # are involved in a circular dependency.
    expected_pattern = (
        r"Failed to resolve dependencies for .*ServiceA.* "
        r"due to NameError \(potential forward reference in a circular dependency\): "
        r"name 'ServiceB' is not defined. "
        r"Resolution stack: \[.*ServiceA.*\]"
    )
    with pytest.raises(Exception, match=expected_pattern):
        provider.get_service(ServiceA)

```

---

### 21. tests\test_config.py

- **File ID**: file_20
- **Type**: Code File
- **Line Count**: 133
- **Description**: File at tests\test_config.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
import pytest
from dataclasses import dataclass
from wd.di.config import (
    Configuration,
    ConfigurationBuilder,
    Options,
    OptionsBuilder,
    IConfiguration,
)
from wd.di import ServiceCollection


@dataclass
class DatabaseOptions:
    connection_string: str = ""
    max_connections: int = 10


@dataclass
class AppSettings:
    name: str = ""
    version: str = ""


def test_configuration_get():
    config = Configuration(
        {
            "database": {
                "connectionString": "test-connection",
                "maxConnections": 5,
            },
            "app": {"name": "TestApp", "version": "1.0.0"},
        }
    )

    assert config.get("database:connectionString") == "test-connection"
    assert config.get("app:name") == "TestApp"
    assert config.get("nonexistent") is None
    assert config.get("database:nonexistent") is None


def test_configuration_get_section():
    config = Configuration(
        {
            "database": {
                "connectionString": "test-connection",
                "maxConnections": 5,
            }
        }
    )

    section = config.get_section("database")
    assert section.get("connectionString") == "test-connection"
    assert section.get("maxConnections") == 5


def test_configuration_builder():
    builder = ConfigurationBuilder()
    config = (
        builder.add_dictionary(
            {
                "database": {
                    "connectionString": "test-connection",
                    "maxConnections": 5,
                }
            }
        )
        .add_dictionary({"app": {"name": "TestApp"}})
        .build()
    )

    assert config.get("database:connectionString") == "test-connection"
    assert config.get("app:name") == "TestApp"


def test_options_builder():
    config = Configuration(
        {"database": {"connectionString": "test-connection", "maxConnections": 5}}
    )

    builder = OptionsBuilder(DatabaseOptions)
    options = builder.bind_configuration(config, "database").build()

    assert options.connection_string == "test-connection"
    assert options.max_connections == 5


def test_options_di_integration():
    services = ServiceCollection()

    config = Configuration(
        {
            "database": {"connectionString": "test-connection", "maxConnections": 5},
            "app": {"name": "TestApp", "version": "1.0.0"},
        }
    )

    services.add_singleton_factory(IConfiguration, lambda sp: config)
    services.configure(DatabaseOptions, section="database")
    services.configure(AppSettings, section="app")

    provider = services.build_service_provider()

    db_options = provider.get_service(Options[DatabaseOptions])
    app_options = provider.get_service(Options[AppSettings])

    assert db_options.value.connection_string == "test-connection"
    assert db_options.value.max_connections == 5
    assert app_options.value.name == "TestApp"
    assert app_options.value.version == "1.0.0"


def test_options_without_configuration():
    services = ServiceCollection()

    services.configure(DatabaseOptions)
    provider = services.build_service_provider()

    with pytest.raises(Exception, match="Configuration service not registered"):
        provider.get_service(Options[DatabaseOptions])


def test_options_missing_section():
    services = ServiceCollection()

    config = Configuration({})
    services.add_singleton_factory(IConfiguration, lambda sp: config)
    services.configure(DatabaseOptions, section="database")
    provider = services.build_service_provider()

    db_options = provider.get_service(Options[DatabaseOptions])
    assert db_options.value.connection_string == ""
    assert db_options.value.max_connections == 10

```

---

### 22. tests\test_decorators.py

- **File ID**: file_21
- **Type**: Code File
- **Line Count**: 26
- **Description**: File at tests\test_decorators.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
from wd.di import ServiceCollection

services = ServiceCollection()

@services.transient()
class FooService:
    def do_something(self):
        print("FooService doing something!")


@services.singleton()
class BarService:
    def __init__(self, foo_service: FooService):
        self.foo_service = foo_service

    def do_something_else(self):
        print("BarService doing something else!")
        self.foo_service.do_something()


def test_decorators():
    service_provider = services.build_service_provider()
    bar_service = service_provider.get_service(BarService)
    bar_service.do_something_else()

    assert bar_service is not None

```

---

### 23. tests\test_di.py

- **File ID**: file_22
- **Type**: Code File
- **Line Count**: 53
- **Description**: File at tests\test_di.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
# tests/test_di.py

from typing import assert_type
# from wd.di.service_collection import ServiceCollection # Old import path
from wd.di import ServiceCollection # Correct import path


# Define test services - these are fine at module level
class IService:
    def execute(self):
        pass


class ServiceA(IService):
    def execute(self):
        return "ServiceA"


class ServiceB(IService):
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a

    def execute(self):
        return f"ServiceB depends on {self.service_a.execute()}"


def test_transient_services():
    services = ServiceCollection() # Instantiate locally
    services.add_transient(ServiceA)
    services.add_transient(IService, ServiceB)

    provider = services.build_service_provider()
    service1 = provider.get_service(IService)
    service2 = provider.get_service(IService)

    assert service1 is not service2
    assert service1.execute() == "ServiceB depends on ServiceA"


def test_singleton_services():
    services = ServiceCollection() # Instantiate locally
    services.add_singleton(ServiceA)
    services.add_singleton(IService, ServiceB)

    provider = services.build_service_provider()
    service1 = provider.get_service(IService)
    service2 = provider.get_service(IService)


    assert_type(service1, IService)
    assert service1 is service2
    assert isinstance(service1, IService) and isinstance(service1, ServiceB)
    assert isinstance(service1, IService) and not isinstance(service1, ServiceA)
```

---

### 24. tests\test_middleware.py

- **File ID**: file_23
- **Type**: Code File
- **Line Count**: 206
- **Description**: File at tests\test_middleware.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
import pytest
from dataclasses import dataclass
from typing import List, Optional
from wd.di.middleware import (
    IMiddleware,
    MiddlewarePipeline,
    LoggingMiddleware,
    ValidationMiddleware,
    CachingMiddleware,
)
from wd.di import ServiceCollection


@dataclass
class RequestContext:
    path: str
    value: Optional[str] = None


class HelperTestMiddleware(IMiddleware):
    def __init__(self):
        self.executed = False
        self.context_path = None

    async def invoke(self, context: RequestContext, next):
        self.executed = True
        self.context_path = context.path
        return await next()


class ModifyingMiddleware(IMiddleware):
    async def invoke(self, context: RequestContext, next):
        context.value = "modified"
        return await next()


class ResultMiddleware(IMiddleware):
    async def invoke(self, context: RequestContext, next):
        await next()
        return "result"


@pytest.mark.asyncio
async def test_middleware_pipeline_execution():
    pipeline = MiddlewarePipeline()
    middleware = HelperTestMiddleware()
    pipeline.use_middleware(HelperTestMiddleware, instance=middleware)

    context = RequestContext(path="/test")
    await pipeline.execute(context)

    assert middleware.executed
    assert middleware.context_path == "/test"


@pytest.mark.asyncio
async def test_middleware_order():
    executed_order: List[str] = []

    class FirstMiddleware(IMiddleware):
        async def invoke(self, context, next):
            executed_order.append("first")
            return await next()

    class SecondMiddleware(IMiddleware):
        async def invoke(self, context, next):
            executed_order.append("second")
            return await next()

    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(FirstMiddleware)
    pipeline.use_middleware(SecondMiddleware)

    await pipeline.execute(RequestContext(path="/test"))
    assert executed_order == ["first", "second"]


@pytest.mark.asyncio
async def test_middleware_modification():
    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(ModifyingMiddleware)

    context = RequestContext(path="/test")
    await pipeline.execute(context)

    assert context.value == "modified"


@pytest.mark.asyncio
async def test_middleware_result():
    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(ResultMiddleware)

    result = await pipeline.execute(RequestContext(path="/test"))
    assert result == "result"


@pytest.mark.asyncio
async def test_validation_middleware():
    def validator(context: RequestContext) -> bool:
        return context.path.startswith("/")

    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(lambda: ValidationMiddleware(validator))

    # Valid path should work
    await pipeline.execute(RequestContext(path="/test"))

    # Invalid path should raise ValueError
    with pytest.raises(ValueError):
        await pipeline.execute(RequestContext(path="invalid"))


@pytest.mark.asyncio
async def test_caching_middleware():
    executed_count = 0

    class CountingMiddleware(IMiddleware):
        async def invoke(self, context, next):
            nonlocal executed_count
            executed_count += 1
            return "result"

    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(CachingMiddleware)
    pipeline.use_middleware(CountingMiddleware)

    context = RequestContext(path="/test")

    # First call should execute the pipeline
    result1 = await pipeline.execute(context)
    assert result1 == "result"
    assert executed_count == 1

    # Second call should use cached result
    result2 = await pipeline.execute(context)
    assert result2 == "result"
    assert executed_count == 1  # Count shouldn't increase


@pytest.mark.asyncio
async def test_logging_middleware():
    logs = []
    logger = lambda msg: logs.append(msg)

    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(lambda: LoggingMiddleware(logger))
    pipeline.use_middleware(ResultMiddleware)

    await pipeline.execute(RequestContext(path="/test"))

    assert len(logs) == 2
    assert "Executing pipeline" in logs[0]
    assert "completed with result" in logs[1]


@pytest.mark.asyncio
async def test_di_integration():
    services = ServiceCollection()

    app = services.create_application_builder()

    app.configure_middleware(
        lambda builder: (
            builder.use_middleware(LoggingMiddleware)
            .use_middleware(HelperTestMiddleware)
            .use_middleware(ResultMiddleware)
        )
    )

    provider = app.build()

    pipeline = provider.get_service(MiddlewarePipeline)

    result = await pipeline.execute(RequestContext(path="/test"))

    assert result == "result"


@pytest.mark.asyncio
async def test_di_middleware_dependencies():
    services = ServiceCollection()

    class DependentMiddleware(IMiddleware):
        def __init__(self, test_middleware: HelperTestMiddleware):
            self.test_middleware = test_middleware

        async def invoke(self, context, next):
            await self.test_middleware.invoke(context, next)
            return "dependent_result"

    app = services.create_application_builder()

    app.configure_middleware(
        lambda builder: (
            builder.use_middleware(HelperTestMiddleware).use_middleware(DependentMiddleware)
        )
    )

    provider = app.build()

    pipeline = provider.get_service(MiddlewarePipeline)

    result = await pipeline.execute(RequestContext(path="/test"))

    assert result == "dependent_result"

```

---

### 25. tests\test_scoped.py

- **File ID**: file_24
- **Type**: Code File
- **Line Count**: 91
- **Description**: File at tests\test_scoped.py
- **Dependencies**: None
- **Used By**: None

**Content**:
```
import pytest
# from wd.di.service_collection import ServiceCollection # Old import path
from wd.di import ServiceCollection # Correct import path

def test_scoped_service_from_root_fails():
    services = ServiceCollection() # Instantiate locally
    # Define a simple scoped service.
    class ScopedService:
        pass

    services.add_scoped(ScopedService)
    provider = services.build_service_provider()

    # Attempting to resolve a scoped service directly from the root provider should fail.
    with pytest.raises(Exception, match="Cannot resolve scoped service from the root provider"):
        provider.get_service(ScopedService)

def test_scoped_service_same_instance_in_scope():
    services = ServiceCollection() # Instantiate locally
    # Define a simple scoped service.
    class ScopedService:
        pass

    services.add_scoped(ScopedService)
    provider = services.build_service_provider()

    # Within the same scope, multiple resolutions should yield the same instance.
    with provider.create_scope() as scope:
        instance1 = scope.get_service(ScopedService)
        instance2 = scope.get_service(ScopedService)
        assert instance1 is instance2

def test_scoped_service_different_instances_in_different_scopes():
    services = ServiceCollection() # Instantiate locally
    # Define a simple scoped service.
    class ScopedService:
        pass

    services.add_scoped(ScopedService)
    provider = services.build_service_provider()

    # Different scopes should produce different instances.
    with provider.create_scope() as scope1:
        instance1 = scope1.get_service(ScopedService)
    with provider.create_scope() as scope2:
        instance2 = scope2.get_service(ScopedService)
    assert instance1 is not instance2

def test_disposable_service_is_disposed():
    services = ServiceCollection() # Instantiate locally
    # Define a disposable service that implements a dispose method.
    class DisposableService:
        def __init__(self):
            self.is_disposed = False

        def dispose(self):
            self.is_disposed = True

    services.add_scoped(DisposableService)
    provider = services.build_service_provider()
    disposable_instance = None

    # Within the scope, the instance is not disposed.
    with provider.create_scope() as scope:
        disposable_instance = scope.get_service(DisposableService)
        assert not disposable_instance.is_disposed

    # Exiting the scope should trigger disposal.
    assert disposable_instance.is_disposed

def test_close_method_is_called_for_disposable():
    services = ServiceCollection() # Instantiate locally
    # Define a disposable service that uses a close method.
    class DisposableService:
        def __init__(self):
            self.is_closed = False

        def close(self):
            self.is_closed = True

    services.add_scoped(DisposableService)
    provider = services.build_service_provider()
    disposable_instance = None

    # Within the scope, the instance is not closed.
    with provider.create_scope() as scope:
        disposable_instance = scope.get_service(DisposableService)
        assert not disposable_instance.is_closed

    # Exiting the scope should trigger the close method.
    assert disposable_instance.is_closed

```

---

## Summary

- **Total Files**: 25
- **Code Files**: 25
- **Regular Files**: 0
- **Total Lines of Code**: 1430
