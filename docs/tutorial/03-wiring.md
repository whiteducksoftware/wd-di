# Tutorial Part 3: Presentation and Wiring It All Up

In this final part of the tutorial, we'll create the Presentation Layer for our Order Processing application and then wire all the components (Domain, Services, Infrastructure, Presentation) together using WD-DI. This will demonstrate how to configure and run the application.

We assume you have an instance of `ServiceCollection` available, created via `sc = create_service_collection()` from `wd.di`.

---

## Presentation Layer

This layer provides the interface to interact with your application. For this tutorial, we'll simulate a simple command-line interface (CLI) interaction point using an `OrderController`.

**File: `presentation/controller.py`** (Conceptual)

```python
# Using Order from domain.models and IOrderService from domain.interfaces (see 01-domain.md)
# from domain.models import Order 
# from domain.interfaces import IOrderService

# Assume sc is an instance of ServiceCollection
# from wd.di import create_service_collection
# sc = create_service_collection()

# @sc.transient() # Controllers are often transient or scoped
class OrderController:
    def __init__(self, order_service: /*IOrderService from domain.interfaces*/ object):
        self.order_service = order_service

    def submit_order_cli(self, order_id: str, item: str, quantity: int, price: float):
        print(f"CLI: Received order submission for ID: {order_id}")
        # In a real CLI, you'd parse arguments here
        # Create the Order model instance
        order_data = { "order_id": order_id, "item": item, "quantity": quantity, "price": price } # Using dict for Order model for simplicity here.
                                                                                                 # Ideally, Order class would be imported and used.
        # Simulate creating an Order object; in a real app, import Order from domain.models
        class TempOrder: # Placeholder for domain.models.Order
            def __init__(self, order_id, item, quantity, price):
                self.order_id = order_id
                self.item = item
                self.quantity = quantity
                self.price = price

        actual_order = TempOrder(order_id=order_id, item=item, quantity=quantity, price=price)
        
        success = self.order_service.process_new_order(actual_order)
        if success:
            print(f"CLI: Order {order_id} processed successfully by the service.")
        else:
            print(f"CLI: Order {order_id} processing failed.")
```
The `OrderController` depends on `IOrderService` to delegate the actual order processing.

---

## Wiring It All Up with WD-DI

Now, let's bring all the pieces together in a `main.py` file. This is where we will:
1.  Create a `ServiceCollection`.
2.  Register all our services (Logger, Repository, Order Service, Controller).
3.  Configure options (like `AppConfig`).
4.  Build the `ServiceProvider`.
5.  Resolve the `OrderController` and simulate an order submission.

**File: `main.py`** (Application Entry Point)

```python
from wd.di import create_service_collection
from wd.di.config import Configuration, Options, IConfiguration

# Assume these are your actual defined classes from the tutorial modules
# (domain/interfaces.py, domain/models.py)
# (infrastructure/logging_service.py, infrastructure/config_models.py)
# (data/repository.py, services/order_processing_service.py, presentation/controller.py)

# --- 0. Define/Import interfaces and models (from Tutorial Part 1: 01-domain.md) ---
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Order:
    order_id: str
    item: str
    quantity: int
    price: float

class IOrderRepository(ABC):
    @abstractmethod
    def save_order(self, order: Order):
        pass
    @abstractmethod
    def get_order_by_id(self, order_id: str) -> Order | None:
        pass

class IOrderService(ABC):
    @abstractmethod
    def process_new_order(self, order: Order) -> bool:
        pass

class ILogger(ABC):
    @abstractmethod
    def log_info(self, message: str):
        pass
    @abstractmethod
    def log_error(self, message: str, exception: Exception | None = None):
        pass

# --- 1. Create ServiceCollection ---
sc = create_service_collection()

# --- 2. Implementations (from Tutorial Part 2: 02-services.md and Presentation Layer) ---

# Infrastructure Layer
@dataclass
class AppConfig:
    service_name: str = "OrderProcessorTutorial"
    default_user: str = "system"
    debug_mode: bool = False

@sc.singleton(ILogger)
class ConsoleLogger(ILogger):
    def log_info(self, message: str):
        print(f"[INFO] {message}")
    def log_error(self, message: str, exception: Exception | None = None):
        err_msg = f"[ERROR] {message}"
        if exception:
            err_msg += f" - Exception: {type(exception).__name__}: {exception}"
        print(err_msg)

# Data Access Layer
@sc.singleton(IOrderRepository)
class InMemoryOrderRepository(IOrderRepository):
    def __init__(self, logger: ILogger):
        self._logger = logger
        self._orders_db: dict[str, Order] = {}
        self._logger.log_info("InMemoryOrderRepository initialized.")

    def save_order(self, order: Order):
        self._logger.log_info(f"DAL: Saving order {order.order_id}")
        self._orders_db[order.order_id] = order
        self._logger.log_info(f"DAL: Order {order.order_id} saved.")

    def get_order_by_id(self, order_id: str) -> Order | None:
        self._logger.log_info(f"DAL: Attempting to retrieve order {order_id}")
        order = self._orders_db.get(order_id)
        if order:
            self._logger.log_info(f"DAL: Order {order_id} found.")
        else:
            self._logger.log_info(f"DAL: Order {order_id} not found.")
        return order

# Service Layer
@sc.singleton(IOrderService)
class OrderProcessingService(IOrderService):
    def __init__(self, order_repository: IOrderRepository, logger: ILogger):
        self._order_repository = order_repository
        self._logger = logger
        self._logger.log_info("OrderProcessingService initialized.")

    def process_new_order(self, order: Order) -> bool:
        self._logger.log_info(f"SERVICE: Processing new order {order.order_id} for item '{order.item}'")
        if order.quantity <= 0 or order.price <= 0:
            self._logger.log_error(f"SERVICE: Invalid order data for {order.order_id}.")
            return False
        self._logger.log_info(f"SERVICE: Order {order.order_id} passed validation.")
        try:
            self._order_repository.save_order(order)
            self._logger.log_info(f"SERVICE: Order {order.order_id} successfully saved.")
            return True
        except Exception as e:
            self._logger.log_error(f"SERVICE: Failed to save order {order.order_id}", exception=e)
            return False

# Presentation Layer
@sc.transient() # Controllers are often transient or scoped
class OrderController:
    def __init__(self, order_service: IOrderService, logger: ILogger, app_config_options: Options[AppConfig]):
        self.order_service = order_service
        self.logger = logger
        self.app_config = app_config_options.value # Access the AppConfig instance
        self.logger.log_info(f"OrderController initialized for service: {self.app_config.service_name}")

    def submit_order_cli(self, order_id: str, item: str, quantity: int, price: float):
        self.logger.log_info(f"CLI: Received order submission for ID: {order_id} by {self.app_config.default_user}")
        order_data = Order(order_id=order_id, item=item, quantity=quantity, price=price)
        success = self.order_service.process_new_order(order_data)
        if success:
            self.logger.log_info(f"CLI: Order {order_id} processed successfully.")
        else:
            self.logger.log_error(f"CLI: Order {order_id} processing failed.")

# --- 3. Configure Options ---
app_config_dict = {
    "App": {
        "ServiceName": "MyAwesomeOrderProcessor",
        "DefaultUser": "TutorialUser",
        "DebugMode": True
    }
}
config_source = Configuration(app_config_dict)
sc.add_singleton_factory(IConfiguration, lambda _: config_source) # Register IConfiguration
sc.configure(AppConfig, section="App") # Configure AppConfig to bind to "App" section

# --- 4. Build ServiceProvider ---
provider = sc.build_service_provider()

# --- 5. Resolve and Use ---
if __name__ == "__main__":
    main_logger = provider.get_service(ILogger)
    main_logger.log_info("Application starting...")

    controller = provider.get_service(OrderController)
    
    # Simulate submitting a valid order
    controller.submit_order_cli(order_id="ORD001", item="Laptop", quantity=1, price=1200.50)
    
    # Simulate submitting an invalid order
    controller.submit_order_cli(order_id="ORD002", item="Mouse", quantity=0, price=25.00)
    
    main_logger.log_info("Application finished.")

---

## Running the Application

To run the `main.py` script developed in this tutorial (which includes all the defined services, interfaces, and the controller), you would typically execute it directly:

```bash
python main.py 
# Ensure main.py is in your current directory or provide the correct path.
```

Upon execution, you should see output similar to the following, demonstrating the logger in action and the flow of the order processing:

```
[INFO] ConsoleLogger initialized.
[INFO] InMemoryOrderRepository initialized.
[INFO] OrderProcessingService initialized.
[INFO] OrderController initialized for service: MyAwesomeOrderProcessor
[INFO] CLI: Received order submission for ID: order123 by TutorialUser
[INFO] SERVICE: Processing new order order123 for item 'Laptop'
[INFO] SERVICE: Order order123 passed validation.
[INFO] DAL: Saving order order123
[INFO] DAL: Order order123 saved.
[INFO] SERVICE: Order order123 successfully saved.
[INFO] CLI: Order order123 processed successfully.
```

This output confirms that:
- Services were initialized as expected (ConsoleLogger, InMemoryOrderRepository, OrderProcessingService, OrderController).
- Configuration (AppConfig with `ServiceName` and `DefaultUser`) was loaded and used by the `OrderController`.
- The `OrderController` successfully invoked the `OrderProcessingService`.
- The `OrderProcessingService` interacted with the `InMemoryOrderRepository`.
- Logging messages were produced at each significant step by the `ConsoleLogger`.

---

## Tutorial Conclusion

In this tutorial, we've built a simple order processing application that demonstrates how to:

- **Separate concerns** by splitting the application into distinct layers (Domain, Data Access, Services, Presentation, Infrastructure).
- **Design using interfaces** (like `ILogger`, `IOrderRepository`, `IOrderService`) and concrete implementations to achieve a flexible, testable codebase.
- **Manage configuration** through strongly-typed options (`AppConfig` bound from a dictionary).
- **Leverage WD-DI** to wire all components together, using `create_service_collection()` and decorators like `@sc.singleton()` and `@sc.transient()` for registering services and managing their lifetimes.

By using WD-DI, you not only simplify dependency management but also establish a solid foundation for building scalable and maintainable Python applications. This design tutorial illustrates that dependency injection is far more than a theoretical concept—it's a practical tool for crafting high-quality software architectures.
