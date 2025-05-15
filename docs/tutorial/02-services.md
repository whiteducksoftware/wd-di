# Tutorial Part 2: Services and Infrastructure

In this part of the tutorial, we'll implement the interfaces defined in the Domain Layer (`01-domain.md`) and set up basic infrastructure components like logging and configuration placeholders. We'll focus on the Data Access Layer, Service Layer (Business Logic), and Infrastructure Layer.

We assume you have an instance of `ServiceCollection` available, created via `sc = create_service_collection()` from `wd.di`.

---

## Infrastructure Layer

Let's start with some basic infrastructure components. These often include logging, configuration models, or clients for external services.

**File: `infrastructure/logging_service.py`** (Conceptual)

```python
# For the tutorial, we'll use interfaces defined in 01-domain.md
# from domain.interfaces import ILogger 

# Assume sc is an instance of ServiceCollection from wd.di
# from wd.di import create_service_collection
# sc = create_service_collection() 

# @sc.singleton(ILogger) # Registering the concrete logger
class ConsoleLogger: # Implements ILogger structurally for simplicity here
    def log_info(self, message: str):
        print(f"[INFO] {message}")

    def log_error(self, message: str, exception: Exception | None = None):
        if exception:
            print(f"[ERROR] {message} - Exception: {exception}")
        else:
            print(f"[ERROR] {message}")
```

**File: `infrastructure/config_models.py`** (Conceptual)

```python
from dataclasses import dataclass

@dataclass
class AppConfig:
    """Represents application-level configuration settings."""
    service_name: str = "OrderProcessorTutorial"
    default_user: str = "system"
    debug_mode: bool = False

@dataclass
class EmailServiceOptions:
    """Configuration specific to an email service."""
    smtp_host: str = "localhost"
    smtp_port: int = 2525 # Default for MailHog/MailCatcher
    sender_address: str = "noreply@example.com"
```
These dataclasses will be used with WD-DI's Options pattern later when we wire everything up.

---

## Data Access Layer (DAL)

This layer is responsible for data persistence. It implements the repository interfaces defined in the Domain Layer.

**File: `data/repository.py`** (Conceptual)

```python
# Using interfaces from domain.interfaces (see 01-domain.md)
# from domain.interfaces import IOrderRepository, ILogger, Order
# from infrastructure.logging_service import ConsoleLogger # Or inject ILogger

# Assume sc is an instance of ServiceCollection
# from wd.di import create_service_collection
# sc = create_service_collection()

# @sc.singleton(IOrderRepository)
class InMemoryOrderRepository: # Implements IOrderRepository structurally
    def __init__(self, logger: /*ILogger from domain.interfaces*/ object):
        self._logger = logger
        self._orders_db = {}
        self._logger.log_info("InMemoryOrderRepository initialized.")

    def save_order(self, order: /*Order from domain.models*/ object):
        self._logger.log_info(f"DAL: Saving order {order.order_id}")
        self._orders_db[order.order_id] = order
        self._logger.log_info(f"DAL: Order {order.order_id} saved.")

    def get_order_by_id(self, order_id: str) -> /*Order | None from domain.models*/ object | None:
        self._logger.log_info(f"DAL: Attempting to retrieve order {order_id}")
        order = self._orders_db.get(order_id)
        if order:
            self._logger.log_info(f"DAL: Order {order_id} found.")
        else:
            self._logger.log_info(f"DAL: Order {order_id} not found.")
        return order
```
For this tutorial, `InMemoryOrderRepository` uses a simple dictionary as an in-memory database. It depends on `ILogger` (which `ConsoleLogger` implements) for logging its actions.

---

## Service Layer (Business Logic)

This layer contains the core business logic of the application. It orchestrates operations using services from the Data Access Layer and other business services.

**File: `services/order_processing_service.py`** (Conceptual)

```python
# Using interfaces and models from domain (see 01-domain.md)
# from domain.interfaces import IOrderService, IOrderRepository, ILogger, Order
# from infrastructure.logging_service import ConsoleLogger # Or inject ILogger

# Assume sc is an instance of ServiceCollection
# from wd.di import create_service_collection
# sc = create_service_collection()

# @sc.singleton(IOrderService)
class OrderProcessingService: # Implements IOrderService structurally
    def __init__(self, 
                 order_repository: /*IOrderRepository*/ object, 
                 logger: /*ILogger*/ object):
        self._order_repository = order_repository
        self._logger = logger
        self._logger.log_info("OrderProcessingService initialized.")

    def process_new_order(self, order: /*Order from domain.models*/ object) -> bool:
        self._logger.log_info(f"SERVICE: Processing new order {order.order_id} for item '{order.item}'")
        
        # Basic validation (example)
        if order.quantity <= 0 or order.price <= 0:
            self._logger.log_error(f"SERVICE: Invalid order data for {order.order_id}. Quantity/Price must be positive.")
            return False
        
        # Simulate some processing, e.g., payment, inventory check (not shown)
        self._logger.log_info(f"SERVICE: Order {order.order_id} passed validation and pre-processing.")
        
        try:
            self._order_repository.save_order(order)
            self._logger.log_info(f"SERVICE: Order {order.order_id} successfully saved by repository.")
            # Here you might trigger notifications, update other systems, etc.
            return True
        except Exception as e:
            self._logger.log_error(f"SERVICE: Failed to save order {order.order_id}", exception=e)
            return False
```
The `OrderProcessingService` implements `IOrderService`. It depends on an `IOrderRepository` to save order data and an `ILogger` for logging. Its `process_new_order` method contains the (simplified) business logic for handling a new order.

In the next part, we'll create the Presentation Layer and wire all these components together using WD-DI.

*(Note: For actual type hints like `/*ILogger from domain.interfaces*/ object`, you would use the real imported types. The comments are for illustrative cross-referencing to `01-domain.md` within this markdown context.)* 