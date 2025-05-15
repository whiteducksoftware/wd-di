# Repository Analysis

## Repository Statistics

- **Extensions analyzed**: .md
- **Number of files analyzed**: 17
- **Total lines of code (approx)**: 2689

## Project Files

### 1. README.md

- **File ID**: file_0
- **Type**: File
- **Line Count**: 82
- **Description**: File at README.md

**Content**:
```
# WD-DI: .NET Style Dependency Injection for Python

<!-- TODO: Add badges here (e.g., PyPI version, build status, code coverage, license) -->
<!-- Example:
[![PyPI version](https://badge.fury.io/py/wd-di.svg)](https://badge.fury.io/py/wd-di)
[![Build Status](https://github.com/your-repo/wd-di/actions/workflows/ci.yml/badge.svg)](https://github.com/your-repo/wd-di/actions)
...
-->

WD-DI brings the robust and flexible dependency injection patterns of .NET to your Python applications, with no external library dependencies—just Python's standard library.

**Full documentation can be found at [your-docs-site.com](https://your-docs-site.com) (or in the `/docs` directory).**

---

## Why WD-DI?

*   **Simplified Dependency Management:** Effortlessly manage object creation and lifecycles.
*   **Enhanced Testability:** Easily mock dependencies for robust unit tests.
*   **Modular Architecture:** Build loosely coupled, maintainable, and scalable applications.
*   **Familiar Patterns:** Leverage .NET-inspired DI concepts like service lifetimes (Singleton, Scoped, Transient), constructor injection, and the Options pattern for configuration.
*   **Pythonic and Lightweight:** Clean, intuitive API that integrates smoothly into your Python projects.

---

## Installation

```bash
pip install wd-di
```

---

## Quick Example: The Power of WD-DI

Experience clean, decoupled code with intuitive type-hinted dependency resolution:

```python
from wd.di import ServiceCollection

# 1. Create a service collection
services = ServiceCollection()

# 2. Define your services (interfaces optional but recommended)
class IEmailService:
    def send(self, message: str): ...

@services.singleton(IEmailService) # Register EmailService as a singleton for IEmailService
class EmailService(IEmailService):
    def send(self, message: str):
        print(f"Sending email: {message}")

@services.transient() # Register NotifierService as transient (new instance each time)
class NotifierService:
    def __init__(self, emailer: IEmailService): # Dependency injected here!
        self._emailer = emailer

    def notify_admin(self, alert: str):
        self._emailer.send(f"Admin Alert: {alert}")

# 3. Build the provider and resolve your top-level service
provider = services.build_service_provider()
notifier = provider.get_service(NotifierService) # Type is inferred!

# 4. Use your services
notifier.notify_admin("System critical!")
# Output: Sending email: Admin Alert: System critical!
```

Dive into the **[full documentation](https://your-docs-site.com)** to explore service lifetimes, configuration, middleware, and more!

---

## Contributing

Contributions are welcome! Please see the main documentation site for details on how to contribute, report issues, or request features.

---

## License

This project is licensed under the terms of the LICENSE file included in the repository.
```

---

### 2. docs\advanced\anti-patterns.md

- **File ID**: file_1
- **Type**: File
- **Line Count**: 397
- **Description**: File at docs\advanced\anti-patterns.md

**Content**:
```
# Common Python Anti-Patterns and DI Solutions

Python's flexibility, while powerful, can lead to common architectural pitfalls if not managed carefully. Using Dependency Injection (DI) as a guiding principle can help avoid these anti-patterns and promote more maintainable, testable, and robust code. WD-DI provides the tools to implement these solutions effectively.

---

## 1. Global State and Singletons (Problem)

**Anti-Pattern:** Relying on globally accessible objects or manually implemented singletons for managing state or services. This makes testing difficult, hides dependencies, and can lead to unpredictable behavior due to shared mutable state.

```python
# global_config.py (Anti-Pattern)
class GlobalConfig:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.api_key = "GlobalSecret!"
        self.debug_mode = True

# Used everywhere in the codebase:
# from global_config import GlobalConfig
# config = GlobalConfig.get_instance()
# if config.debug_mode:
#     print(f"API Key: {config.api_key}")
```

**DI Solution:** Manage such configurations or shared services as singletons within the DI container. Access them via constructor injection where needed.

```python
# DI Solution
from dataclasses import dataclass
from wd.di import create_service_collection
from wd.di.config import Options, IConfiguration, Configuration # Assuming IConfiguration and Configuration are set up

sc = create_service_collection()

@dataclass
class AppConfig:
    api_key: str = "DefaultKey"
    debug_mode: bool = False

# Setup: Register IConfiguration and configure AppConfig
# This would typically be done once at application startup.
config_values = {"app": {"api_key": "LoadedFromConfig", "debug_mode": True}}
actual_configuration = Configuration(config_values)
sc.add_singleton_factory(IConfiguration, lambda _: actual_configuration) # Or add_instance
sc.configure(AppConfig, section="app")

@sc.singleton()
class MyConfiguredService:
    def __init__(self, app_opts: Options[AppConfig]):
        self.config = app_opts.value # Access the strongly-typed config
    
    def perform_action(self):
        if self.config.debug_mode:
            print(f"Running in DEBUG. API Key: {self.config.api_key}")
        else:
            print("Running in PRODUCTION.")

# Usage
# provider = sc.build_service_provider()
# service = provider.get_service(MyConfiguredService)
# service.perform_action()
```
**Benefits:** Dependencies are explicit, configuration is testable (mock `Options[AppConfig]`), and the DI container manages the singleton lifetime.

---

## 2. Hidden Dependencies and Import-Time Side Effects (Problem)

**Anti-Pattern:** Modules or classes that create resources (like database connections) or have significant side effects upon import. This makes it hard to manage resource lifetimes and to test components in isolation.

```python
# database.py (Anti-Pattern)
# import sqlite3

# Global connection created at import time - hard to manage and test
# db_connection = sqlite3.connect("application.db") 

# class UserRepository:
#     def get_user_by_id(self, user_id):
#         cursor = db_connection.cursor()
#         cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
#         return cursor.fetchone()
```

**DI Solution:** Define interfaces for dependencies like database access. Register implementations with appropriate lifetimes (e.g., scoped or transient for connections/sessions, singleton for connection pools/factories). Inject these interfaces into services.

```python
# DI Solution
from abc import ABC, abstractmethod
import sqlite3 # For the example implementation
from wd.di import create_service_collection

sc = create_service_collection()

class IDatabaseConnection(ABC):
    @abstractmethod
    def execute(self, query: str, params: tuple) -> list:
        pass
    @abstractmethod
    def close(self):
        pass # For proper resource management, e.g. in a scoped lifetime

# Implementation (could be scoped in a real app)
@sc.transient(IDatabaseConnection) # Often scoped or transient
class SqliteConnectionWrapper(IDatabaseConnection):
    def __init__(self, db_path: str = ":memory:"): # db_path could come from config
        print(f"SqliteConnectionWrapper created for {db_path}")
        self.connection = sqlite3.connect(db_path)
    
    def execute(self, query: str, params: tuple) -> list:
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def close(self):
        print("SqliteConnectionWrapper closing connection.")
        self.connection.close()

@sc.singleton()
class UserRepository:
    def __init__(self, db_conn_factory: IDatabaseConnection): # Injects a transient connection
        self.db_conn = db_conn_factory # Or a factory that provides connections
    
    def get_user_by_id(self, user_id: int) -> list:
        # In a real app, connection lifecycle (open/close) would be managed carefully,
        # often by using the connection as a context manager if it supports it,
        # or by having the DI scope manage its disposal (e.g. via close method).
        data = self.db_conn.execute("SELECT ? AS id, ? AS name", (user_id, "Test"))
        # self.db_conn.close() # If transient, scope would call close if disposable
        return data

# Usage
# provider = sc.build_service_provider()
# with provider.create_scope() as scope:
#     user_repo = scope.get_service(UserRepository)
#     user = user_repo.get_user_by_id(123)
#     print(f"User from repo: {user}")
# The SqliteConnectionWrapper's close() method would be called on scope disposal.
```
**Benefits:** Resource creation is managed by DI, promoting better lifetime control and testability (mock `IDatabaseConnection`).

---

## 3. Module-Level Functions Creating Tight Coupling (Problem)

**Anti-Pattern:** Using module-level functions that directly call other module-level functions across different parts of your application. This can lead to a tangled web of dependencies that are hard to trace and test, and can easily result in circular import issues if not careful.

```python
# user_processing.py (Anti-Pattern)
# import order_processing # Potential circular import risk
# 
# def get_user_summary(user_id):
#     user_details = {"id": user_id, "name": "Some User"} # fetch_user_from_db(user_id)
#     user_orders = order_processing.get_orders_for_user(user_id)
#     return {**user_details, "orders": user_orders}

# order_processing.py (Anti-Pattern)
# import user_processing # Potential circular import risk
# 
# def get_orders_for_user(user_id):
#     # May need user details for some logic, leading to circular call
#     # if user_processing.is_user_premium(user_id):
#     #     return [{"id": "premium_order_123"}]
#     return [{"id": "order_abc", "items": 2}, {"id": "order_xyz", "items": 1}]
```

**DI Solution:** Encapsulate logic within classes (services) and define clear interfaces. Inject dependencies via constructors. This breaks circular dependencies at the module import level and makes them manageable (or highlights problematic circular logic) at the service resolution level.

```python
# DI Solution
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from wd.di import create_service_collection

sc = create_service_collection()

class IOrderService(ABC):
    @abstractmethod
    def get_orders_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        pass

class IUserService(ABC):
    @abstractmethod
    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        pass

@sc.singleton(IOrderService)
class OrderService(IOrderService):
    # If OrderService needed IUserService, it would be injected here.
    # For this example, assume it does not to keep it simple.
    def get_orders_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        print(f"OrderService: Getting orders for {user_id}")
        return [{f"order_id": f"{user_id}_order1"}]

@sc.singleton(IUserService)
class UserService(IUserService):
    def __init__(self, order_service: IOrderService):
        self._order_service = order_service
    
    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        print(f"UserService: Getting summary for {user_id}")
        user_details = {"id": user_id, "name": f"User {user_id}"}
        user_orders = self._order_service.get_orders_for_user(user_id)
        return {**user_details, "orders": user_orders}

# Usage
# provider = sc.build_service_provider()
# user_service_instance = provider.get_service(IUserService)
# summary = user_service_instance.get_user_summary("USR456")
# print(f"User Summary: {summary}")
```
**Benefits:** Dependencies are explicit through constructor injection. Circular dependencies become easier to identify and manage at the class/service level. Testing is simplified by mocking injected interfaces.

---

## 4. Monolithic Classes with Mixed Responsibilities (Problem)

**Anti-Pattern:** Large classes that handle too many concerns (e.g., data access, business logic, notifications, logging all in one class). This violates the Single Responsibility Principle, making the class hard to understand, modify, and test.

```python
# class GodUserManager(AntiPattern):
#     def __init__(self):
#         # self.db = connect_db()
#         # self.mailer = setup_mailer()
#         # self.logger = setup_logger()
#         pass
# 
#     def create_user_and_notify(self, email, password):
#         # self.logger.info(f"Attempting to create {email}")
#         # user = self.db.save_user(email, password)
#         # self.mailer.send_welcome_email(email)
#         # self.logger.info(f"User {email} created and notified.")
#         pass
```

**DI Solution:** Break down monolithic classes into smaller, focused services, each with a single responsibility. Use DI to inject these fine-grained services where needed.

```python
# DI Solution
from abc import ABC, abstractmethod
from wd.di import create_service_collection

sc = create_service_collection()

# Define Interfaces (examples)
class IUserRepository(ABC):
    @abstractmethod
    def save_user(self, email: str, password: str) -> dict:
        pass

class IEmailService(ABC):
    @abstractmethod
    def send_welcome_email(self, email: str):
        pass

class ILogger(ABC):
    @abstractmethod
    def info(self, message: str):
        pass

# Concrete Implementations (simplified examples, register with @sc decorators)
@sc.singleton(ILogger)
class ConsoleLogger(ILogger):
    def info(self, message: str):
        print(f"[INFO] {message}")

@sc.singleton(IEmailService)
class EmailService(IEmailService):
    def __init__(self, logger: ILogger):
        self.logger = logger
    def send_welcome_email(self, email: str):
        self.logger.info(f"EmailService: Sending welcome email to {email}")

@sc.singleton(IUserRepository)
class UserRepository(IUserRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger
    def save_user(self, email: str, password: str) -> dict:
        self.logger.info(f"UserRepository: Saving user {email}")
        return {"id": "user_123", "email": email}

# Main orchestrating service
@sc.singleton()
class UserCreationService:
    def __init__(self, repo: IUserRepository, mailer: IEmailService, logger: ILogger):
        self._repo = repo
        self._mailer = mailer
        self._logger = logger
    
    def create_user_and_notify(self, email: str, password: str):
        self._logger.info(f"UserCreationService: Attempting to create {email}")
        user = self._repo.save_user(email, password)
        self._mailer.send_welcome_email(email)
        self._logger.info(f"UserCreationService: User {email} created and notified.")
        return user

# Usage
# provider = sc.build_service_provider()
# user_creator = provider.get_service(UserCreationService)
# new_user = user_creator.create_user_and_notify("test@example.com", "password123")
# print(f"New user created: {new_user}")
```
**Benefits:** Each service has a clear responsibility, improving code clarity, reusability, and testability. Changes to one aspect (e.g., email sending logic) are isolated to one service.

---

## 5. Static Methods and Utility Classes (Problem)

**Anti-Pattern:** Overuse of static methods or utility classes with many static functions for common operations (e.g., validation, calculation). While sometimes convenient, they can become dependency sinks, are hard to mock for testing, and don't fit well into an object-oriented design that relies on polymorphism or swappable implementations.

```python
# class PaymentUtils(AntiPattern):
#     @staticmethod
#     def calculate_tax(amount):
#         return amount * 0.20 # Fixed tax rate
# 
#     @staticmethod
#     def is_card_valid(card_number):
#         return len(card_number) == 16
# 
# class OldOrderProcessor:
#     def process_order(self, amount, card):
#         if PaymentUtils.is_card_valid(card):
#             total_with_tax = amount + PaymentUtils.calculate_tax(amount)
#             # ... process payment ...
#             return total_with_tax
#         raise ValueError("Invalid card")
```

**DI Solution:** Encapsulate such logic into services (even small, focused ones) with well-defined interfaces. These services can then be injected and easily mocked or replaced.

```python
# DI Solution
from abc import ABC, abstractmethod
from wd.di import create_service_collection

sc = create_service_collection()

class ITaxCalculator(ABC):
    @abstractmethod
    def calculate_tax(self, amount: float) -> float:
        pass

class ICardValidator(ABC):
    @abstractmethod
    def is_card_valid(self, card_number: str) -> bool:
        pass

@sc.singleton(ITaxCalculator)
class DefaultTaxCalculator(ITaxCalculator):
    def calculate_tax(self, amount: float) -> float:
        return amount * 0.20 # Example: 20% tax

@sc.singleton(ICardValidator)
class StandardCardValidator(ICardValidator):
    def is_card_valid(self, card_number: str) -> bool:
        return len(card_number) == 16 # Simple validation

@sc.singleton()
class NewOrderProcessor:
    def __init__(self, tax_calc: ITaxCalculator, card_validator: ICardValidator):
        self._tax_calc = tax_calc
        self._card_validator = card_validator
    
    def process_order(self, amount: float, card_number: str) -> float:
        if not self._card_validator.is_card_valid(card_number):
            raise ValueError("Invalid card number provided.")
        
        tax_amount = self._tax_calc.calculate_tax(amount)
        total_with_tax = amount + tax_amount
        print(f"Processing payment for: {total_with_tax} (Amount: {amount}, Tax: {tax_amount})")
        # ... actual payment processing logic ...
        return total_with_tax

# Usage
# provider = sc.build_service_provider()
# order_processor = provider.get_service(NewOrderProcessor)
# try:
#     total = order_processor.process_order(100.00, "1234567890123456")
#     print(f"Order processed successfully. Total: {total}")
#     order_processor.process_order(50.00, "invalidcard")
# except ValueError as e:
#     print(f"Error processing order: {e}")
```
**Benefits:** Utility logic becomes part of the DI-managed object graph. Implementations can be swapped (e.g., different tax calculators for different regions). Services are easily testable by mocking their dependencies (e.g., mock `ITaxCalculator`).

---

By recognizing these anti-patterns and applying DI principles, you can build more flexible, robust, and maintainable Python applications with WD-DI. 
```

---

### 3. docs\advanced\circular-deps.md

- **File ID**: file_2
- **Type**: File
- **Line Count**: 91
- **Description**: File at docs\advanced\circular-deps.md

**Content**:
```
# Circular Dependency Detection

Circular dependencies occur when two or more services depend on each other directly or indirectly, creating a loop that cannot be resolved. For example, Service A depends on Service B, and Service B depends on Service A. Such a situation can lead to infinite recursion during instantiation if not detected.

WD-DI is designed to detect and report these circular dependencies at runtime, preventing your application from crashing due to stack overflows or unresolvable states.

---

## How WD-DI Detects Circular Dependencies

WD-DI uses a `ContextVar` (a context-local variable, ensuring thread/task safety for asynchronous applications) to keep track of the set of services that are currently in the process of being resolved for a given request chain.

When you request a service from the `ServiceProvider` (or a `Scope`):
1.  Before attempting to create an instance of the requested service, WD-DI adds the service's unique key (usually its type or interface) to this `ContextVar` set.
2.  If the service has dependencies, WD-DI recursively attempts to resolve them.
3.  If, during this recursive resolution, WD-DI encounters a request for a service key that is already present in the `ContextVar` set for the current resolution path, it means a circular dependency has been detected.
4.  Once the service (and its dependencies) are successfully resolved, its key is removed from the `ContextVar` set for that path, allowing other independent resolutions of the same service type if needed (e.g., for transient services requested multiple times by different branches of a dependency graph).

This mechanism ensures that a circular loop is caught before it can cause an infinite instantiation loop.

---

## `CircularDependencyError`

When a circular dependency is detected, WD-DI raises a `wd.di.errors.CircularDependencyError`. This error typically includes a message indicating the service type that caused the cycle and often the chain of dependencies involved.

---

## Example of a Circular Dependency

Consider two services, `ServiceA` and `ServiceB`, that depend on each other:

```python
from wd.di import create_service_collection
from wd.di.errors import CircularDependencyError

sc = create_service_collection()

# Forward declaration for type hints if classes are in the same scope
class ServiceB: ...

@sc.singleton()
class ServiceA:
    def __init__(self, b: ServiceB): # ServiceA depends on ServiceB
        self.b = b
        print("ServiceA created")

@sc.singleton()
class ServiceB:
    def __init__(self, a: ServiceA): # ServiceB depends on ServiceA
        self.a = a
        print("ServiceB created")

# --- Attempt to resolve ---
provider = sc.build_service_provider()

try:
    # Requesting either ServiceA or ServiceB will trigger the error
    service_a = provider.get_service(ServiceA)
except CircularDependencyError as e:
    print(f"Caught expected error: {e}")
    # Example error message might be:
    # "Circular dependency detected while resolving type <class '__main__.ServiceA'>. Resolution path: {<class '__main__.ServiceA'>, <class '__main__.ServiceB'>}"

# Expected Output (simplified, actual message might vary slightly):
# Caught expected error: Circular dependency detected for service <class '__main__.ServiceA'>. Current resolution path: {<ServiceKey for ServiceA>, <ServiceKey for ServiceB>}
```

In this scenario:
1.  Resolving `ServiceA` requires `ServiceB`. `ServiceA` is added to the resolution stack.
2.  Resolving `ServiceB` (for `ServiceA`) requires `ServiceA`. `ServiceB` is added to the resolution stack.
3.  Attempting to resolve `ServiceA` (for `ServiceB`) finds `ServiceA` already in the resolution stack, triggering `CircularDependencyError`.

---

## Resolving Circular Dependencies

If you encounter a `CircularDependencyError`, it's a signal that your application's design has a problematic dependency loop. WD-DI does not provide mechanisms to "break" the cycle automatically (e.g., with lazy proxies for one of the dependencies) because circular dependencies often indicate a deeper architectural issue.

The recommended ways to resolve circular dependencies are:

1.  **Refactor your services:**
    *   **Interface Segregation:** Introduce an interface that one of the services can depend on, and have the other service implement it. This can sometimes break the direct cycle if the interface is more focused.
    *   **Mediator Pattern:** Introduce a third service (a mediator) that both services depend on. The original services then communicate through the mediator rather than directly.
    *   **Re-evaluate Responsibilities:** Often, a circular dependency suggests that one or both services are doing too much or that responsibilities are not clearly separated. Splitting services into smaller, more focused units can help.
2.  **Property/Method Injection (Use with Caution):**
    *   While constructor injection is preferred, you could, in some rare cases, break a cycle by having one service set a dependency on another via a property or method after both are constructed. This is generally not recommended as it makes dependencies less explicit and can lead to objects being in an incompletely initialized state. WD-DI focuses on constructor injection.
3.  **Eventual Consistency/Callbacks:**
    *   Instead of a direct synchronous dependency, one service might raise an event that the other service subscribes to, decoupling them.

The best approach is usually to refactor the dependencies to eliminate the circularity, leading to a cleaner and more understandable architecture. 
```

---

### 4. docs\advanced\scaling.md

- **File ID**: file_3
- **Type**: File
- **Line Count**: 257
- **Description**: File at docs\advanced\scaling.md

**Content**:
```
# Scaling Your Application with WD-DI: Layered Architecture

Structuring your application into layers (e.g., Domain, Data Access, Application/Service, Presentation, Infrastructure) is a common and effective pattern for managing complexity and enhancing scalability and maintainability. WD-DI helps manage dependencies *between* these layers cleanly.

**Principle:**
Organize your code into distinct layers, each with a specific responsibility. Use Dependency Injection to provide dependencies to classes within a layer or from a lower layer to an upper layer. Avoid direct dependencies from lower layers to upper layers.

**Example: Layered Application**

Let's assume we have a `ServiceCollection` instance, `sc`, created via `sc = create_service_collection()`.

**Domain Layer:** Defines core business entities and interfaces.

```python
from abc import ABC, abstractmethod
# sc = create_service_collection() # Assume sc is available globally for these snippets for brevity

class IOrderService(ABC):
    @abstractmethod
    def process_order(self, order_id: str):
        pass

# OrderService would typically be in an Application/Service Layer
# For this example, let's imagine it's simple enough or defined elsewhere.
```

**Data Access Layer (Repository Pattern):** Handles data persistence.

```python
# from abc import ABC, abstractmethod # Already imported
# class IOrderService(ABC): ... # Defined above

class IOrderRepository(ABC):
    @abstractmethod
    def get_order(self, order_id: str) -> dict:
        pass
    @abstractmethod
    def save_order(self, order_data: dict):
        pass # Added save_order for completeness

# Example implementation for IOrderRepository
# @sc.singleton(IOrderRepository) # Decorator would be on the concrete class
# class OrderRepository(IOrderRepository):
#     def get_order(self, order_id: str) -> dict:
#         print(f"DAL: Getting order {order_id} from database.")
#         return {"id": order_id, "item": "Book from DB", "status": "Pending"}
#     def save_order(self, order_data: dict):
#         print(f"DAL: Saving order {order_data.get('id')} to database.")
```

**Application/Service Layer:** Contains business logic and orchestrates tasks, using services from the Domain and Data Access layers.

```python
# from abc import ABC, abstractmethod # Already imported
# class IOrderService(ABC): ... # Defined above
# class IOrderRepository(ABC): ... # Defined above

# @sc.singleton(IOrderService) # Decorator for OrderService implementation
# class OrderService(IOrderService):
#     def __init__(self, order_repo: IOrderRepository):
#         self.order_repo = order_repo
#
#     def process_order(self, order_id: str):
#         print(f"APP: Processing order {order_id}")
#         order = self.order_repo.get_order(order_id)
#         # ... some business logic ...
#         order["status"] = "Processed"
#         self.order_repo.save_order(order)
#         print(f"APP: Order {order_id} processed and saved.")
```

**Presentation Layer (e.g., Controller):** Handles user interaction or API requests and uses services from the Application Layer.

```python
# class IOrderService(ABC): ... # Defined above

# @sc.transient() # Controllers are often transient
# class OrderController:
#     def __init__(self, order_service: IOrderService):
#         self.order_service = order_service
#
#     def handle_web_request_for_order(self, order_id_from_request: str):
#         print(f"PRES: Received request for order {order_id_from_request}")
#         self.order_service.process_order(order_id_from_request)
#         print(f"PRES: Order {order_id_from_request} processing initiated.")
```

**Infrastructure Layer:** Contains cross-cutting concerns like logging, external service clients, etc. These can be injected into any layer where needed.

```python
# Example: A simple logger (could be more complex and registered via its own interface)
# @sc.singleton() # Registering a concrete logger as a singleton
# class ConsoleLogger:
#     def log(self, message: str):
#         print(f"[LOG] {message}")

# An OrderService might then take ILogger (if defined) or ConsoleLogger:
# class OrderService(IOrderService):
#     def __init__(self, order_repo: IOrderRepository, logger: ConsoleLogger):
#         self.order_repo = order_repo
#         self.logger = logger
#         # ... rest of the implementation ...
```

**Assembling and Running the Application (Illustrative)**

To make the above runnable, you'd need concrete classes and actual registration. Here's a more complete, self-contained example showing how these decorated classes would be registered and used:

```python
from abc import ABC, abstractmethod
from wd.di import create_service_collection

sc = create_service_collection()

# --- Interfaces (Domain Layer) ---
class IOrderRepository(ABC):
    @abstractmethod
    def get_order(self, order_id: str) -> dict:
        pass
    @abstractmethod
    def save_order(self, order_data: dict):
        pass

class IOrderService(ABC):
    @abstractmethod
    def process_order(self, order_id: str):
        pass

class ILogger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass_a

# --- Implementations (Various Layers) ---
@sc.singleton(ILogger)
class ConsoleLogger(ILogger):
    def log(self, message: str):
        print(f"[LOG] {message}")

@sc.singleton(IOrderRepository)
class OrderRepository(IOrderRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def get_order(self, order_id: str) -> dict:
        self.logger.log(f"DAL: Getting order {order_id} from database.")
        return {"id": order_id, "item": "Book from DB", "status": "Pending"}
    
    def save_order(self, order_data: dict):
        self.logger.log(f"DAL: Saving order {order_data.get('id')} to database.")

@sc.singleton(IOrderService)
class OrderService(IOrderService):
    def __init__(self, order_repo: IOrderRepository, logger: ILogger):
        self.order_repo = order_repo
        self.logger = logger

    def process_order(self, order_id: str):
        self.logger.log(f"APP: Processing order {order_id}")
        order = self.order_repo.get_order(order_id)
        # ... some business logic ...
        order["status"] = "Processed"
        self.order_repo.save_order(order)
        self.logger.log(f"APP: Order {order_id} processed and saved.")

@sc.transient() # Controllers are often transient or scoped
class OrderController:
    def __init__(self, order_service: IOrderService, logger: ILogger):
        self.order_service = order_service
        self.logger = logger

    def handle_web_request_for_order(self, order_id_from_request: str):
        self.logger.log(f"PRES: Received request for order {order_id_from_request}")
        self.order_service.process_order(order_id_from_request)
        self.logger.log(f"PRES: Order {order_id_from_request} processing initiated.")

# --- Build and Run ---
provider = sc.build_service_provider()

controller = provider.get_service(OrderController)
controller.handle_web_request_for_order("order123")

# Expected Output:
# [LOG] PRES: Received request for order order123
# [LOG] APP: Processing order order123
# [LOG] DAL: Getting order order123 from database.
# [LOG] DAL: Saving order order123 to database.
# [LOG] APP: Order order123 processed and saved.
# [LOG] PRES: Order order123 processing initiated.
```

**When to use Layered Architecture:**
Build a layered architecture using WD-DI to cleanly separate business logic, data access, presentation, and infrastructure concerns. This enhances maintainability, testability (as layers can be tested in isolation by mocking adjacent layers), and scalability by allowing individual layers to be developed, deployed, and scaled independently (to some extent).

This approach helps in:
*   **Separation of Concerns:** Each layer has a well-defined responsibility.
*   **Maintainability:** Changes in one layer are less likely to impact other layers.
*   **Testability:** Layers can be tested independently by mocking dependencies from other layers.
*   **Scalability:** Different layers can potentially be scaled independently if the architecture allows (e.g., multiple instances of the presentation layer).

WD-DI facilitates this by making the dependencies between these layers explicit and manageable.

---

### Start Simple, Then Expand

**Principle:**
Begin with a minimal DI setup. As your project grows, you can introduce more sophisticated patterns like layered architectures, detailed interface-driven design, middleware pipelines, and dynamic configuration incrementally.

**Example:**

```python
from wd.di import create_service_collection
# Assume some services are defined, e.g.:
# class DatabaseService: ...
# class UserService: ...
# class LoggingMiddleware: # (from wd.di.middleware or custom)
#     async def invoke(self, context, next_call): ...

sc = create_service_collection()

# Initial phase: Register core services (decorators make this concise)
# @sc.singleton()
# class DatabaseService:
#     def connect(self):
#         print("DB Connected")
# @sc.singleton()
# class UserService:
#     def __init__(self, db: DatabaseService):
#         self.db = db
#     def get_user(self):
#         self.db.connect()
#         print("User fetched")

# provider = sc.build_service_provider()
# user_service = provider.get_service(UserService)
# user_service.get_user()

# Later, as the project evolves, integrate additional layers and middleware:
# (Assuming LoggingMiddleware is defined and UserService, DatabaseService are decorated)

# app_builder = sc.create_application_builder()
# app_builder.configure_middleware(lambda builder: (
#     builder.use_middleware(LoggingMiddleware) # Middleware needs to be DI-aware or resolvable
# ))
# # provider_with_middleware = app_builder.build()
# # Now, resolving services from provider_with_middleware will allow middleware pipeline execution (if pipeline is invoked)
```

**When to use:**
Adopt an incremental approach to DI. 
1. Start by registering your main services, perhaps using decorators for conciseness.
2. As complexity grows, introduce interfaces to decouple components further.
3. For cross-cutting concerns (logging, auth, error handling), implement a middleware pipeline.
4. Utilize the options pattern for robust configuration management as your application needs to support different environments or settings.

This evolutionary approach allows your architecture to adapt to the project's needs without over-engineering from the start. 
```

---

### 5. docs\core-concepts\component-based-design.md

- **File ID**: file_4
- **Type**: File
- **Line Count**: 138
- **Description**: File at docs\core-concepts\component-based-design.md

**Content**:
```
# Component-Based Design with Interfaces and Lifetimes

Component-based design focuses on building systems from loosely coupled, replaceable parts (components). In the context of DI, this often involves defining clear interfaces (contracts) for your services and then providing concrete implementations for these interfaces. Managing the lifetime of these components is also a crucial aspect.

---

## Interface-Driven Development

**Principle:**
Define interfaces (typically Abstract Base Classes - ABCs in Python) for your services. Register your concrete service implementations against these interfaces. This allows you to easily swap out implementations (e.g., for different environments or for testing) without changing the code that uses the service.

**Example:**

```python
from abc import ABC, abstractmethod
from wd.di import create_service_collection

# Create a service collection instance
sc = create_service_collection()

# Define an interface for user repository
class IUserRepository(ABC):
    @abstractmethod
    def get_user(self, user_id: str) -> dict:
        pass

# Implementation of the repository interface
@sc.singleton(IUserRepository) # Register UserRepository as the singleton for IUserRepository
class UserRepository(IUserRepository):
    def get_user(self, user_id: str) -> dict:
        # In a real app, this would fetch from a database
        print(f"UserRepository: Getting user {user_id}")
        return {"id": user_id, "name": "John Doe"}

# Another possible implementation (e.g., for testing or a different data source)
# Note: To use a named registration or switch implementations, you might need
# to manage multiple ServiceCollection instances or clear and re-register for tests.
# Standard resolution gets the last registered default for an interface.
@sc.singleton(IUserRepository) # This would overwrite the previous registration for IUserRepository
class MockUserRepository(IUserRepository):
    def get_user(self, user_id: str) -> dict:
        print(f"MockUserRepository: Getting user {user_id}")
        return {"id": user_id, "name": "Mock User"}

# --- Usage ---
# If MockUserRepository was registered last, it will be the one resolved:
provider = sc.build_service_provider()
user_repo = provider.get_service(IUserRepository)
print(user_repo.get_user("123"))
# Expected output if MockUserRepository was last:
# MockUserRepository: Getting user 123
# {'id': '123', 'name': 'Mock User'}

# To truly switch, you'd typically manage registrations carefully:
sc_default = create_service_collection()
@sc_default.singleton(IUserRepository)
class RealUserRepository(IUserRepository):
    def get_user(self, user_id: str) -> dict:
        return {"id": user_id, "name": "Real User from DB"}

sc_test = create_service_collection()
@sc_test.singleton(IUserRepository)
class TestDoubleUserRepository(IUserRepository):
    def get_user(self, user_id: str) -> dict:
        return {"id": user_id, "name": "Test User via Double"}

# In app code:
# provider_real = sc_default.build_service_provider()
# repo_real = provider_real.get_service(IUserRepository)

# In test code:
# provider_test = sc_test.build_service_provider()
# repo_test = provider_test.get_service(IUserRepository)
```

**When to use Interface-Driven Development:**
Always prefer to code against interfaces rather than concrete implementations when a component is likely to have multiple implementations (e.g., for different data sources, different external services) or when you want to improve testability by easily mocking dependencies.

---

## Lifetimes Matter

**Principle:**
Select service lifetimes based on the nature of the dependency and how it should be shared:

*   **`@sc.transient()` (Transient):** A new instance of the service is created every time it is requested from the service provider or injected as a dependency.
    *   **Use for:** Lightweight, stateless services or services that should not share state between different consumers within the same scope or across scopes.
*   **`@sc.singleton()` (Singleton):** Only one instance of the service is created for the entire lifetime of the service provider (application). This single instance is shared across all requests and scopes.
    *   **Use for:** Services that are expensive to create, stateless utility services, or services that need to maintain a global application state (use with caution for shared mutable state).
*   **`@sc.scoped()` (Scoped):** A new instance of the service is created once per scope. Within the same scope (e.g., a web request, or a manually created scope via `provider.create_scope()`), the same instance is reused. Different scopes will get different instances.
    *   **Use for:** Services that need to maintain state for a specific unit of work (like a web request or a transaction) but should be isolated between different units of work. Examples include database session/connection objects, or services holding request-specific cache.

**Example (Conceptual Registration):**

```python
from wd.di import create_service_collection
# For demonstration, assume IService and various implementations are defined.
# class IService:
#     def do_work(self): raise NotImplementedError
# class MyTransientServiceImpl(IService): 
#     def __init__(self): print(f"{type(self).__name__} created")
#     def do_work(self): print(f"{type(self).__name__} working")
# class MySingletonServiceImpl(IService):
#     def __init__(self): print(f"{type(self).__name__} created")
#     def do_work(self): print(f"{type(self).__name__} working")
# class MyScopedServiceImpl(IService):
#     def __init__(self): print(f"{type(self).__name__} created")
#     def do_work(self): print(f"{type(self).__name__} working")

sc = create_service_collection()

# Manual registration (less common now with decorators but still possible):
# sc.add_transient(IService, MyTransientServiceImpl)
# sc.add_singleton(IService, MySingletonServiceImpl)
# sc.add_scoped(IService, MyScopedServiceImpl)

# Using decorators (preferred):
# @sc.transient(IService)
# class DecoratedTransient(IService): ...

# @sc.singleton(IService)
# class DecoratedSingleton(IService): ...

# @sc.scoped(IService)
# class DecoratedScoped(IService): ...

# If decorating the class itself as the service type:
# @sc.transient()
# class MyPlainTransientService:
#     def __init__(self): print(f"{type(self).__name__} created")
#     def do_work(self): print(f"{type(self).__name__} working")
```

**When to Choose Lifetimes:**
Carefully consider the statefulness and resource implications of your services. 
- Use **transient** for stateless services or those needing unique instances.
- Use **singleton** for shared, stateless utilities or for managing global state carefully.
- Use **scoped** for services that need to maintain state within a specific unit of work (like a request) and be disposed of afterward. 
```

---

### 6. docs\core-concepts\configuration.md

- **File ID**: file_5
- **Type**: File
- **Line Count**: 93
- **Description**: File at docs\core-concepts\configuration.md

**Content**:
```
# Configuration and Options Pattern

WD-DI includes a robust configuration system inspired by .NET's Options pattern. This allows you to bind configuration data (from dictionaries, JSON files, environment variables, etc., though currently focused on dictionary sources) to strongly-typed Python dataclasses. This approach centralizes configuration logic, provides type safety, and makes configuration access clean and maintainable.

---

## Key Components

*   **`IConfiguration`:** An interface (and its concrete implementation `Configuration`) that represents your application's configuration. It can load data from a dictionary and provides methods to access configuration sections.
*   **`Options[T]`:** A generic wrapper class. When you request `Options[MyConfigClass]`, WD-DI provides an instance of `Options` whose `value` attribute holds a populated instance of `MyConfigClass`.
*   **`services.configure(ConfigClass, section_name)`:** A method on `ServiceCollection` used to bind a section of your application's configuration (retrieved from `IConfiguration`) to a specific dataclass (`ConfigClass`).

---

## How It Works

1.  **Define an Options Dataclass:** Create a Python dataclass that represents the structure of a particular configuration section.
    ```python
    from dataclasses import dataclass

    @dataclass
    class DatabaseOptions:
        connection_string: str = ""
        max_connections: int = 10
        timeout: int = 30
    ```
2.  **Provide Configuration Data:** Create a configuration source. Typically, this is a dictionary, which could be loaded from a JSON file, environment variables, or constructed in code.
    ```python
    config_data = {
        "Database": {  # Section name (case-insensitive by default in GetSection)
            "ConnectionString": "your_db_connection_string",
            "MaxConnections": 50
            # Timeout will use the default from DatabaseOptions (30)
        },
        "Logging": {
            "Level": "Information"
        }
    }
    ```
3.  **Register `IConfiguration`:** Add your configuration object (an instance of `Configuration` or your custom `IConfiguration` implementation) to the service collection, usually as a singleton.
    ```python
    from wd.di import create_service_collection
    from wd.di.config import Configuration, IConfiguration

    sc = create_service_collection()
    app_config = Configuration(config_data)
    sc.add_singleton_factory(IConfiguration, lambda _: app_config)
    ```
4.  **Bind Configuration to Options:** Use `sc.configure()` to tell WD-DI how to map a configuration section to your options dataclass.
    ```python
    sc.configure(DatabaseOptions, section="Database")
    ```
    This tells WD-DI: "When `Options[DatabaseOptions]` is requested, find the 'Database' section in `IConfiguration`, create an instance of `DatabaseOptions`, and populate it with data from that section (automatically converting PascalCase/camelCase keys from config to snake_case attributes in the dataclass)."
5.  **Inject `Options[T]` into Services:** In your services, depend on `Options[YourConfigClass]` to access the configured values.
    ```python
    from wd.di.config import Options

    @sc.singleton()
    class DatabaseService:
        def __init__(self, db_options: Options[DatabaseOptions]):
            self.options = db_options.value # Access the populated dataclass instance
            print(f"DB Connection: {self.options.connection_string}")
            print(f"DB Max Connections: {self.options.max_connections}")
            print(f"DB Timeout: {self.options.timeout}") # Will be 30 (default)

    # --- Usage ---
    provider = sc.build_service_provider()
    db_service = provider.get_service(DatabaseService)
    # Expected Output:
    # DB Connection: your_db_connection_string
    # DB Max Connections: 50
    # DB Timeout: 30
    ```

---

## Benefits of the Options Pattern

*   **Strong Typing:** Configuration is accessed via dataclasses, providing attribute access and type checking (if using static analysis). This reduces errors caused by typos in string-based dictionary lookups.
*   **Centralization:** Configuration logic is defined in one place (your options dataclasses and the `configure` calls).
*   **Decoupling:** Services depend on `Options[T]` rather than directly on `IConfiguration` or concrete configuration sources. This makes services more testable, as you can easily provide mock `Options` in tests.
*   **Default Values:** Dataclasses allow you to specify default values for configuration properties, simplifying setup for common scenarios.
*   **Clear Structure:** Configuration is organized into logical sections represented by different options classes.

---

## When to Use

*   For any application settings that might vary between environments (development, staging, production) or need to be managed externally.
*   When you want to provide type-safe access to configuration values within your services.
*   To keep your services decoupled from the specifics of how configuration is loaded and stored.

The Options pattern is a powerful tool for managing application settings in a clean, robust, and maintainable way.

```

---

### 7. docs\core-concepts\constructor-injection.md

- **File ID**: file_6
- **Type**: File
- **Line Count**: 142
- **Description**: File at docs\core-concepts\constructor-injection.md

**Content**:
```
# Constructor Injection

Constructor injection is the primary mechanism by which WD-DI manages and provides dependencies to your services. When a service is resolved, WD-DI inspects its constructor (`__init__` method), identifies the required dependencies based on type hints, and automatically supplies instances of those dependencies.

This pattern promotes clear, testable, and maintainable code by making a class's dependencies explicit in its constructor signature.

---

## How It Works

1.  **Service Registration:** You register your services (e.g., `DatabaseService`, `UserService`) with the `ServiceCollection`, specifying their lifetimes.
2.  **Type Hinting:** Your service constructors must use type hints for their parameters (e.g., `db_service: DatabaseService`). WD-DI uses these hints to know which registered service to inject.
3.  **Resolution:** When you request a service (e.g., `provider.get_service(UserService)`), WD-DI:
    *   Finds the registered entry for `UserService`.
    *   Inspects its `__init__` method.
    *   Sees it needs a `DatabaseService`.
    *   Resolves an instance of `DatabaseService` (according to its registered lifetime).
    *   Instantiates `UserService`, passing the `DatabaseService` instance into its constructor.
    *   Returns the fully constructed `UserService` instance.

---

## Example

Let's consider a `UserService` that depends on a `DatabaseService`.

```python
from wd.di import ServiceCollection

services = ServiceCollection()

# Assume DatabaseService is defined and registered, for example:
# (This could be an interface IUserService or a concrete class)
class IDatabaseService: # Using an interface for demonstration
    def query(self, sql: str):
        raise NotImplementedError

@services.singleton(IDatabaseService) # Registering concrete type for the interface
class ConcreteDatabaseService(IDatabaseService):
    def __init__(self):
        print("ConcreteDatabaseService created (singleton)")

    def query(self, sql: str):
        print(f"Executing query: {sql}")
        return [{"id": 1, "name": "Test User"}] # Dummy data

# UserService depends on IDatabaseService
@services.singleton() # UserService itself can be a singleton or other lifetime
class UserService:
    def __init__(self, db_service: IDatabaseService): # Dependency is type-hinted
        print("UserService created, injecting IDatabaseService.")
        self.db = db_service

    def get_user_data(self, user_id: int):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# --- Usage ---
# Build the service provider
provider = services.build_service_provider()

# Resolve the UserService
# WD-DI will automatically create and inject ConcreteDatabaseService
user_service = provider.get_service(UserService)

# Use the service
user_data = user_service.get_user_data(user_id=1)
print(f"User data retrieved: {user_data}")

# If you resolve IDatabaseService directly, you get the same singleton instance
db_instance = provider.get_service(IDatabaseService)
print(f"Is user_service.db the same as db_instance? {user_service.db is db_instance}")

# Expected Output:
# ConcreteDatabaseService created (singleton)
# UserService created, injecting IDatabaseService.
# Executing query: SELECT * FROM users WHERE id = 1
# User data retrieved: [{'id': 1, 'name': 'Test User'}]
# Is user_service.db the same as db_instance? True
```

In this example:
*   `ConcreteDatabaseService` is registered as a singleton for the `IDatabaseService` interface.
*   `UserService` declares its dependency on `IDatabaseService` in its constructor.
*   When `UserService` is resolved, WD-DI provides the singleton instance of `ConcreteDatabaseService`.

---

## Benefits of Constructor Injection

*   **Explicit Dependencies:** A class's dependencies are clearly listed in its constructor signature, making the class's requirements easy to understand.
*   **Improved Testability:** When unit testing, you can easily pass mock or stub implementations of dependencies directly to the constructor, isolating the class under test. For example:
    ```python
    # --- Defining services (simplified for testability example) ---
    from abc import ABC, abstractmethod

    class IEmailService(ABC):
        @abstractmethod
        def send_email(self, recipient: str, subject: str, body: str):
            pass

    class UserService:
        def __init__(self, email_service: IEmailService):
            self.email_service = email_service

        def notify_user(self, user_id: str, message: str):
            # In a real app, fetch user's email, etc.
            email_address = f"{user_id}@example.com"
            self.email_service.send_email(email_address, "Notification", message)

    # --- Test with a mock --- 
    class MockEmailService(IEmailService):
        def __init__(self):
            self.sent_emails = []

        def send_email(self, recipient: str, subject: str, body: str):
            print(f"MOCK: Sending email to {recipient} - Subject: {subject}")
            self.sent_emails.append({"to": recipient, "subject": subject, "body": body})

    def test_user_service_notification():
        mock_mailer = MockEmailService()
        # Manually inject the mock when creating UserService for the test
        user_service_for_test = UserService(email_service=mock_mailer)
        
        user_service_for_test.notify_user("testuser", "Your item has shipped!")
        
        assert len(mock_mailer.sent_emails) == 1
        assert mock_mailer.sent_emails[0]["to"] == "testuser@example.com"
        assert mock_mailer.sent_emails[0]["body"] == "Your item has shipped!"
        print("Test passed: UserService correctly used the mock email service.")

    # To run the test (typically done by a test runner like pytest):
    # test_user_service_notification()
    ```
*   **Loose Coupling:** Classes don't create their dependencies; they receive them. This reduces coupling between components.
*   **Compile-Time Safety (with Type Hints):** While Python is dynamically typed, type hints used for DI allow static analysis tools (like MyPy) to catch potential type mismatches early.
*   **Readability and Maintainability:** Makes the flow of dependencies through your application easier to trace and manage.

---

**When to use:**

Always prefer constructor injection for mandatory dependencies. It's the cleanest and most straightforward way to implement Inversion of Control and Dependency Injection. WD-DI is designed primarily around this pattern. 
```

---

### 8. docs\core-concepts\lifetimes.md

- **File ID**: file_7
- **Type**: File
- **Line Count**: 181
- **Description**: File at docs\core-concepts\lifetimes.md

**Content**:
```
# Service Lifetimes

Service lifetimes define how instances of services are created, shared, and disposed of by the `ServiceProvider`. WD-DI supports three distinct lifetimes, allowing you to control the instantiation behavior of your registered services precisely.

Choosing the correct lifetime is crucial for managing resources efficiently and ensuring predictable behavior in your application.

---

## Transient

**What is it?**  
A new instance of a transient service is created every time it is requested from the service container. This is the default lifetime if none is specified (though explicit declaration is always clearer).

**Characteristics:**
*   Each call to `provider.get_service(MyTransientService)` or resolution of `MyTransientService` as a dependency will result in a brand-new object.
*   Suitable for lightweight, stateless services where each consumer needs a unique instance.

**Example:**

```python
from wd.di import ServiceCollection

# Assume IRequestProcessor and RequestProcessorImpl are defined
# interface IRequestProcessor: ...
# class RequestProcessorImpl(IRequestProcessor): ...

services = ServiceCollection()

# Registering with explicit implementation type:
services.add_transient(IRequestProcessor, RequestProcessorImpl)

# Or, using the decorator on the class itself (if it implements itself):
@services.transient()
class UniqueOperationLogger:
    def __init__(self):
        import uuid
        self.operation_id = uuid.uuid4()
        print(f"Logger {self.operation_id} created.")

    def log(self, message: str):
        print(f"[{self.operation_id}] {message}")

# --- Usage ---
provider = services.build_service_provider()

logger1 = provider.get_service(UniqueOperationLogger)
logger2 = provider.get_service(UniqueOperationLogger)

print(f"Are loggers the same instance? {logger1 is logger2}")
# Expected Output:
# Logger <uuid1> created.
# Logger <uuid2> created.
# Are loggers the same instance? False
```

**When to use:**
*   Lightweight, stateless services.
*   Services that need to be unique for each user or processing unit (e.g., a request-specific calculator).
*   When you want to avoid any risk of shared state between different parts of your application using the same service type.

---

## Singleton

**What is it?**  
A single instance of a singleton service is created the first time it is requested (or when `build_service_provider` is called if pre-instantiation is configured, though WD-DI resolves lazily by default). This same instance is then shared across the entire application for all subsequent requests within the same service provider.

**Characteristics:**
*   The first resolution creates the instance; all subsequent resolutions return that same instance.
*   Suitable for services that are expensive to create, maintain a shared state, or represent a global resource (e.g., application configuration, logging service, database connection pool manager).

**Example:**

```python
from wd.di import ServiceCollection

# Assume IApplicationSettings and ApplicationSettingsImpl are defined
# interface IApplicationSettings: ...
# class ApplicationSettingsImpl(IApplicationSettings): def load_settings(self): print("Settings loaded.")

services = ServiceCollection()

# Registering with explicit implementation type:
services.add_singleton(IApplicationSettings, ApplicationSettingsImpl)

# Or, using the decorator:
@services.singleton()
class AppConfig:
    def __init__(self):
        print("AppConfig initialized (once).")
        self.api_key = "my-secret-key"

# --- Usage ---
provider = services.build_service_provider()

config1 = provider.get_service(AppConfig)
config2 = provider.get_service(AppConfig)

print(f"Config1 API Key: {config1.api_key}")
print(f"Are configs the same instance? {config1 is config2}")
# Expected Output:
# AppConfig initialized (once).
# Config1 API Key: my-secret-key
# Are configs the same instance? True
```

**When to use:**
*   Services that manage shared state (e.g., caches, application-wide counters).
*   Services that are expensive to initialize and can be reused (e.g., HTTP clients with connection pooling, database access layers).
*   Configuration objects or logging services.
*   **Caution:** Be mindful of thread safety if the singleton service has mutable state that can be accessed concurrently.

---

## Scoped

**What is it?**  
A single instance of a scoped service is created for each defined "scope." Within a given scope, all requests for the service will return the same instance. Different scopes will each get their own unique instance.

**Characteristics:**
*   WD-DI requires explicit scope creation using `provider.create_scope()`.
*   Scoped services are typically created once per scope and disposed of when the scope ends (if they implement a `dispose()` or `close()` method).
*   This lifetime is ideal for services that should share state within a specific unit of work (e.g., a web request, a transaction) but should be isolated between different units of work.

**Example:**

```python
from wd.di import ServiceCollection

# Assume IUnitOfWork and UnitOfWorkImpl are defined
# interface IUnitOfWork: ...
# class UnitOfWorkImpl(IUnitOfWork): def __init__(self): print("UnitOfWork created for scope.")

services = ServiceCollection()

# Registering with explicit implementation type:
services.add_scoped(IUnitOfWork, UnitOfWorkImpl)

# Or, using the decorator:
@services.scoped()
class RequestContext:
    def __init__(self):
        import uuid
        self.request_id = uuid.uuid4()
        print(f"RequestContext {self.request_id} created for current scope.")

# --- Usage ---
provider = services.build_service_provider()

print("--- Scope 1 ---")
with provider.create_scope() as scope1:
    context1_a = scope1.get_service(RequestContext)
    context1_b = scope1.get_service(RequestContext)
    print(f"Are context1_a and context1_b the same? {context1_a is context1_b}")

print("\\n--- Scope 2 ---")
with provider.create_scope() as scope2:
    context2_a = scope2.get_service(RequestContext)
    context2_b = scope2.get_service(RequestContext)
    print(f"Are context2_a and context2_b the same? {context2_a is context2_b}")
    print(f"Is context1_a the same as context2_a? {context1_a is context2_a}")

# Expected Output:
# --- Scope 1 ---
# RequestContext <uuid1> created for current scope.
# Are context1_a and context1_b the same? True
#
# --- Scope 2 ---
# RequestContext <uuid2> created for current scope.
# Are context2_a and context2_b the same? True
# Is context1_a the same as context2_a? False
```

**When to use:**
*   Services that manage resources tied to a specific unit of work, like database connections or transaction contexts, ensuring proper setup and cleanup per scope.
*   Services that need to maintain state for a particular operation or request but should not be shared globally.
*   In web applications, often used for services per HTTP request.

---

Understanding and correctly applying these service lifetimes is fundamental to building robust and efficient applications with WD-DI. 
```

---

### 9. docs\core-concepts\separation-of-concerns.md

- **File ID**: file_8
- **Type**: File
- **Line Count**: 41
- **Description**: File at docs\core-concepts\separation-of-concerns.md

**Content**:
```
# Separation of Concerns

**Principle:**
Break your application into components with clear responsibilities. Use constructor injection to make dependencies explicit and decouple components.

**Example:**

```python
from wd.di import create_service_collection

# Create a service collection instance
sc = create_service_collection()

# EmailService: A service responsible for sending emails
@sc.singleton() # Registering EmailService as a singleton
class EmailService:
    def send_email(self, recipient: str, subject: str, body: str):
        print(f"Sending email to {recipient} with subject '{subject}' and body '{body}'")

# UserService: Depends on EmailService for notifications
@sc.singleton()
class UserService:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    def notify(self, user_id: str, message: str):
        # In a real app, fetch user's email from a repository, etc.
        email_address = f"{user_id}@example.com" # Example email
        self.email_service.send_email(email_address, "Notification", message)

# Register and use the services:
provider = sc.build_service_provider()
user_service = provider.get_service(UserService)
user_service.notify("user123", "Your order has shipped!")

# Expected Output:
# Sending email to user123@example.com with subject 'Notification' and body 'Your order has shipped!'
```

**When to use:**
Apply separation of concerns to keep business logic distinct from infrastructure (e.g., sending emails, logging), making your code easier to maintain and test. 
```

---

### 10. docs\getting-started.md

- **File ID**: file_9
- **Type**: File
- **Line Count**: 89
- **Description**: File at docs\getting-started.md

**Content**:
```
# Getting Started with WD-DI 🚀

This guide will walk you through installing WD-DI and show you a quick example to get you up and running in minutes ⏱️.

## Installation 📦

WD-DI is available on PyPI. You can install it using pip:

```bash
pip install wd-di
```

That's it! 🎉 WD-DI has no external library dependencies, relying only on Python's standard library.

## 5-Minute Tutorial: Your First DI Application 🛠️

Let's build a very simple application to demonstrate the core concepts of WD-DI: registering services, injecting dependencies, and resolving them.

Imagine you have a `NotifierService` that needs an `IEmailService` to send notifications 📧.

```python
from wd.di import ServiceCollection

# 1. Create a service collection ⚙️
# This is the heart of your DI setup, managing all your service registrations.
services = ServiceCollection()

# 2. Define your services 📝
# It's good practice to define interfaces (Abstract Base Classes in Python)
# for your services to promote loose coupling.

class IEmailService:
    def send(self, message: str):
        """Interface for an email sending service."""
        raise NotImplementedError

# This is a concrete implementation of IEmailService.
# The @services.singleton(IEmailService) decorator registers this class
# as the singleton implementation for IEmailService. 🌍
@services.singleton(IEmailService)
class EmailService(IEmailService):
    def send(self, message: str):
        print(f"Sending email: {message}")

# NotifierService depends on IEmailService.
# The @services.transient() decorator means a new instance of NotifierService
# will be created each time it's requested. ⏳
@services.transient()
class NotifierService:
    # WD-DI will automatically inject an instance of IEmailService here. 💉
    def __init__(self, emailer: IEmailService):
        self._emailer = emailer

    def notify_admin(self, alert: str):
        self._emailer.send(f"Admin Alert: {alert}")

# 3. Build the service provider 🏭
# Once all services are registered, build the provider.
# The provider is responsible for resolving service instances.
provider = services.build_service_provider()

# 4. Resolve and use your services ✨
# Request an instance of NotifierService from the provider.
# WD-DI automatically infers the return type if using type hints.
notifier = provider.get_service(NotifierService)

# Now you can use your fully wired service.
notifier.notify_admin("System critical!")
# Expected Output:
# Sending email: Admin Alert: System critical!
```

**What happened here?** 🤔

1.  We created a `ServiceCollection` to hold our service registrations.
2.  We defined an interface `IEmailService` and its implementation `EmailService`. `EmailService` was registered as a singleton, meaning only one instance will be created and shared.
3.  We defined `NotifierService` which depends on `IEmailService`. It was registered as transient, meaning a new instance is created each time.
4.  When `NotifierService` was resolved, WD-DI saw its constructor required an `IEmailService`. It then looked up the registered implementation (`EmailService`), created/retrieved its instance, and passed it to the `NotifierService` constructor.
5.  The `notifier` instance we got back was fully formed with its `EmailService` dependency automatically handled. 👍

This simple example showcases the power of constructor injection and declarative service registration using decorators. Your components don't need to know how to create their dependencies; they just declare what they need, and WD-DI handles the rest.

## Next Steps 🗺️

You're now ready to explore more advanced features of WD-DI! 

*   Dive into **[Core Concepts](./core-concepts/lifetimes.md)** to understand service lifetimes, constructor injection in more detail, and configuration.
*   Learn about the **[Middleware Pipeline](./middleware/overview.md)** for handling cross-cutting concerns.
*   Explore the **[Tutorial](./tutorial/01-domain.md)** for a step-by-step guide to building a more complex application. 
```

---

### 11. docs\index.md

- **File ID**: file_10
- **Type**: File
- **Line Count**: 57
- **Description**: File at docs\index.md

**Content**:
```
# WD-DI: .NET Style Dependency Injection for Python 🐍

WD-DI is a lightweight dependency injection library for Python inspired by .NET's DI system. It provides a robust and flexible way to manage dependencies and lifetimes in your applications. For the Python purists: WD-DI needs no external libraries, just Python standard libraries!  purity ✨

This documentation will guide you 🗺️ through installing WD-DI, understanding its core concepts, and leveraging its advanced features to build well-structured and maintainable Python applications.

---

## Features Overview 🚀

WD-DI supports a variety of dependency injection patterns and configurations, including:

*   **Service Lifetimes:** Control how instances are created and shared (Transient ⏳, Singleton 🌍, Scoped 🎯).
*   **Constructor Injection:** Automatically resolve and inject dependencies into your services 🛠️.
*   **Configuration Binding:** Strongly-typed options pattern for managing application settings ⚙️.
*   **Middleware Pipelines:** Compose processing logic for cross-cutting concerns 🔗.
*   **Scoped Service Management:** Explicit scope creation and automatic disposal of resources 🗑️.
*   **Instance Registration:** Register pre-created objects with the DI container 📦.
*   **Circular Dependency Detection:** Safeguards against infinite recursion in your dependency graph 🔄.

Each feature is designed to promote clear, testable, and maintainable code. Detailed explanations and examples for these can be found in the **Core Concepts**, **Middleware**, and **Advanced Features** sections.

---

## Why Use Dependency Injection? 🤔

Dependency Injection (DI) is a design pattern that allows for the creation of loosely coupled components. Instead of components creating their own dependencies, they are "injected" from an external source (the DI container). This leads to:

*   **Improved Testability:** Dependencies can be easily mocked or stubbed in unit tests 🧪.
*   **Enhanced Modularity:** Components are more independent and easier to replace or reconfigure 🧩.
*   **Better Code Organization:** Clear separation of concerns and responsibilities 🗂️.
*   **Increased Flexibility:** Easier to manage complex object lifecycles and configurations 🤸.

WD-DI brings these benefits to Python in a way that is familiar to developers experienced with .NET's DI system, while remaining Pythonic and lightweight.

---

## Example Application 💡

For a comprehensive walkthrough of building an application using WD-DI, check out the **[Tutorial](./tutorial/01-domain.md)**. It demonstrates how to structure an application with layers, manage dependencies, and integrate various WD-DI features.

---

## Best Practices ✅

When using WD-DI, consider the following best practices:

1.  **Constructor Injection:** Always prefer constructor injection to clearly state dependencies.
2.  **Interface Segregation:** Register services against interfaces (Abstract Base Classes in Python) for flexibility.
3.  **Strongly-Typed Configuration:** Utilize the Options pattern for managing configurations.
4.  **Middleware Separation:** Keep middleware focused on single responsibilities.

---

## License 📜

This project is licensed under the terms of the LICENSE file included in the repository. 
```

---

### 12. docs\middleware\built-ins.md

- **File ID**: file_11
- **Type**: File
- **Line Count**: 249
- **Description**: File at docs\middleware\built-ins.md

**Content**:
```
# Built-in Middleware Components

WD-DI provides a few common middleware components out of the box to handle typical cross-cutting concerns. These can be used directly in your pipeline or serve as examples for creating your own custom middleware.

You can find these middleware classes in the `wd.di.middleware` module.

---

## `LoggingMiddleware`

**Purpose:** Logs the start and completion of pipeline execution for a given context.

**How it works:**
*   Accepts a `logger` callable (e.g., `print`, or a method from Python's `logging` module) in its constructor.
*   Before calling `await next()`, it logs a message like "Executing pipeline for context: [context]".
*   After `await next()` completes, it logs a message like "Pipeline for context: [context] completed with result: [result]".

**Example Usage:**
```python
from wd.di import ServiceCollection
from wd.di.middleware import LoggingMiddleware, MiddlewarePipeline

# Define a context and a simple final handler
class MyContext:
    def __init__(self, data):
        self.data = data
    def __str__(self): # For logging
        return f"MyContext(data='{self.data}')"

class FinalHandler:
    async def invoke(self, context, next):
        return f"Processed: {context.data}"

services = ServiceCollection()
app_builder = services.create_application_builder()

# Configure logging middleware (using print as the logger)
app_builder.configure_middleware(lambda builder: (
    builder
    .use_middleware(lambda: LoggingMiddleware(logger_func=print)) # Pass the logger function
    .use_middleware(FinalHandler)
))

provider = app_builder.build()
pipeline = provider.get_service(MiddlewarePipeline)

# import asyncio
# asyncio.run(pipeline.execute(MyContext("test_data")))
# Expected Output (will vary slightly based on actual context string representation):
# Executing pipeline for context: MyContext(data='test_data')
# Pipeline for context: MyContext(data='test_data') completed with result: Processed: test_data
```
**Dependencies:**
*   Requires a `logger_func: Callable[[str], None]` to be passed to its constructor. This function will be called with log messages.

---

## `ExceptionHandlerMiddleware`

**Purpose:** Centralizes error handling within the middleware pipeline. Catches exceptions from subsequent middleware and allows for custom error processing.

**How it works:**
*   Accepts an `exception_handler` callable in its constructor. This handler function should take the `context` and the `exception` as arguments.
*   It wraps the `await next()` call in a `try...except` block.
*   If an exception occurs, it calls the provided `exception_handler(context, exception)`. The return value of this handler becomes the result of the pipeline execution.

**Example Usage:**
```python
from wd.di import ServiceCollection
from wd.di.middleware import ExceptionHandlerMiddleware, MiddlewarePipeline

class MyContext:
    def __init__(self, should_fail: bool):
        self.should_fail = should_fail

class RiskyHandler:
    async def invoke(self, context, next):
        if context.should_fail:
            raise ValueError("Something went wrong in RiskyHandler!")
        return "RiskyHandler succeeded"

def my_custom_error_handler(context, exception):
    print(f"Custom Error Handler: Caught {type(exception).__name__}: {exception} for context: {context}")
    return "Default error response"

services = ServiceCollection()
app_builder = services.create_application_builder()

app_builder.configure_middleware(lambda builder: (
    builder
    .use_middleware(lambda: ExceptionHandlerMiddleware(my_custom_error_handler))
    .use_middleware(RiskyHandler)
))

provider = app_builder.build()
pipeline = provider.get_service(MiddlewarePipeline)

# import asyncio
# async def main():
#     success_context = MyContext(should_fail=False)
#     result_success = await pipeline.execute(success_context)
#     print(f"Result (Success): {result_success}")

#     fail_context = MyContext(should_fail=True)
#     result_fail = await pipeline.execute(fail_context)
#     print(f"Result (Fail): {result_fail}")
# asyncio.run(main())

# Expected Output:
# Result (Success): RiskyHandler succeeded
# Custom Error Handler: Caught ValueError: Something went wrong in RiskyHandler! for context: <__main__.MyContext object at 0x...>
# Result (Fail): Default error response
```

**Dependencies:**
*   Requires an `exception_handler: Callable[[Any, Exception], Any]` to be passed to its constructor.

---

## `ValidationMiddleware`

**Purpose:** Validates the context object before allowing the pipeline to proceed.

**How it works:**
*   Accepts a `validator` callable in its constructor. This validator function should take the `context` as an argument and return `True` if valid, or `False` (or raise an exception) if invalid.
*   If the `validator(context)` returns `False` or raises an error (by default, it raises `ValueError` if the validator returns `False`), the pipeline is short-circuited, and an exception is raised (or propagated).

**Example Usage:**
```python
from wd.di import ServiceCollection
from wd.di.middleware import ValidationMiddleware, MiddlewarePipeline

class MyContext:
    def __init__(self, data: str):
        self.data = data

class EchoHandler:
    async def invoke(self, context, next):
        return f"Echo: {context.data}"

def my_validator(context: MyContext) -> bool:
    is_valid = context.data is not None and len(context.data) > 3
    print(f"Validating '{context.data}': {is_valid}")
    return is_valid

services = ServiceCollection()
app_builder = services.create_application_builder()

app_builder.configure_middleware(lambda builder: (
    builder
    .use_middleware(lambda: ValidationMiddleware(my_validator))
    .use_middleware(EchoHandler)
))

provider = app_builder.build()
pipeline = provider.get_service(MiddlewarePipeline)

# import asyncio
# async def main():
#     valid_context = MyContext("valid_data")
#     result_valid = await pipeline.execute(valid_context)
#     print(f"Result (Valid): {result_valid}")

#     invalid_context = MyContext("bad")
#     try:
#         await pipeline.execute(invalid_context)
#     except ValueError as e:
#         print(f"Error (Invalid): {e}")
# asyncio.run(main())

# Expected Output:
# Validating 'valid_data': True
# Result (Valid): Echo: valid_data
# Validating 'bad': False
# Error (Invalid): Context validation failed.
```

**Dependencies:**
*   Requires a `validator: Callable[[Any], bool]` to be passed to its constructor.

---

## `CachingMiddleware`

**Purpose:** Caches the result of the pipeline execution for a given context to avoid re-computation.

**How it works:**
*   Uses the `context` object itself as the cache key (so the context must be hashable).
*   On first execution for a specific context, it calls `await next()` and stores the result in an in-memory dictionary.
*   On subsequent executions with an identical (hash-equal) context, it returns the cached result directly without calling `await next()`.

**Example Usage:**
```python
from wd.di import ServiceCollection
from wd.di.middleware import CachingMiddleware, MiddlewarePipeline
import time

# Make context hashable
from dataclasses import dataclass

@dataclass(frozen=True) # frozen=True makes it hashable
class MyContext:
    key: str

call_count = 0
class SlowHandler:
    async def invoke(self, context, next):
        nonlocal call_count
        call_count += 1
        print(f"SlowHandler called (call #{call_count}) for key: {context.key}")
        await asyncio.sleep(0.1) # Simulate work
        return f"Processed: {context.key}"

services = ServiceCollection()
app_builder = services.create_application_builder()

app_builder.configure_middleware(lambda builder: (
    builder
    .use_middleware(CachingMiddleware) # CachingMiddleware should usually be early in the pipeline
    .use_middleware(SlowHandler)
))

provider = app_builder.build()
pipeline = provider.get_service(MiddlewarePipeline)

# import asyncio
# async def main():
#     context1 = MyContext("data_key_1")
#     print(await pipeline.execute(context1)) # First call, SlowHandler executes
#     print(await pipeline.execute(context1)) # Second call, result is cached

#     context2 = MyContext("data_key_2")
#     print(await pipeline.execute(context2)) # First call for this context, SlowHandler executes
# asyncio.run(main())

# Expected Output:
# SlowHandler called (call #1) for key: data_key_1
# Processed: data_key_1
# Processed: data_key_1  (from cache, SlowHandler not called again for context1)
# SlowHandler called (call #2) for key: data_key_2
# Processed: data_key_2
```

**Dependencies:**
*   None, beyond the context being hashable.

---

These built-in middleware components provide a good starting point for handling common concerns. You can easily combine them with your own custom middleware to build sophisticated processing pipelines. 
```

---

### 13. docs\middleware\overview.md

- **File ID**: file_12
- **Type**: File
- **Line Count**: 145
- **Description**: File at docs\middleware\overview.md

**Content**:
```
# Middleware Pipeline Overview

WD-DI includes a flexible middleware pipeline that allows you to compose processing logic in a sequence. This pattern is particularly well-suited for handling cross-cutting concerns in your application—functionality that applies to many parts of your system but isn't part of the core business logic of any single component.

Think of a middleware pipeline as a series of processing steps that a request (or a context object representing that request) goes through. Each middleware component in the pipeline has the opportunity to:

*   Inspect the request/context.
*   Modify the request/context.
*   Perform actions before or after the next middleware in the pipeline is called.
*   Short-circuit the pipeline and return a response immediately.

---

## Common Use Cases for Middleware

*   **Logging:** Recording details about incoming requests and outgoing responses.
*   **Authentication/Authorization:** Verifying credentials and checking permissions.
*   **Error Handling:** Catching exceptions from later middleware or handlers and formatting appropriate error responses.
*   **Caching:** Serving cached responses for certain requests to improve performance.
*   **Request/Response Manipulation:** Modifying headers, transforming data formats.
*   **Validation:** Validating incoming data before it reaches core business logic.

---

## Defining Middleware (`IMiddleware`)

To create a middleware component, you implement the `IMiddleware` interface (or more accurately, a class with an `async def invoke(self, context, next)` method, as Python uses structural subtyping here).

*   **`context`**: An object representing the current request or operation. You define the structure of this context object based on your application's needs.
*   **`next`**: An awaitable callable that invokes the next middleware in the pipeline. You **must** `await next()` to pass control to the subsequent middleware. If you don't call it, the pipeline short-circuits at your middleware.

**Example of a custom middleware:**

```python
from wd.di.middleware import IMiddleware # IMiddleware is a type hint helper

class CustomAuthMiddleware: # Implements IMiddleware structurally
    async def invoke(self, context, next_middleware):
        # Example: Assume context has an 'is_authenticated' attribute
        if not getattr(context, 'is_authenticated', False):
            # You might raise an error or set a response indicating unauthorized
            raise PermissionError("User not authenticated.")
        
        print("User is authenticated, proceeding...")
        
        # Call the next middleware in the pipeline
        response = await next_middleware()
        
        # You can also process the response after it comes back up the chain
        print("CustomAuthMiddleware finished.")
        return response
```

---

## Configuring the Pipeline

WD-DI uses a `MiddlewareBuilder` (obtained via `services.create_application_builder().configure_middleware(...)`) to configure the pipeline. You chain `use_middleware` calls to add middleware components in the desired order of execution.

**Example:**

```python
from wd.di import create_service_collection
from wd.di.middleware import LoggingMiddleware # An example built-in
# from .custom_middleware import CustomAuthMiddleware # Assuming CustomAuthMiddleware is defined

# For demonstration, let's define CustomAuthMiddleware and a dummy context here
class CustomAuthMiddleware:
    async def invoke(self, context, next_middleware):
        if not getattr(context, 'is_authenticated', False):
            raise PermissionError("User not authenticated.")
        print(f"Auth: User authenticated for path {context.path}")
        response = await next_middleware()
        return response

class DummyFinalHandler: # Represents the end of your main processing logic
    async def invoke(self, context, next_middleware): # next_middleware won't be called here
        print(f"Handler: Processing context for path {context.path}")
        return f"Successfully processed {context.path}"

class RequestContext:
    def __init__(self, path: str, is_authenticated: bool = False):
        self.path = path
        self.is_authenticated = is_authenticated

sc = create_service_collection()

# Create an application builder from the service collection
app_builder = sc.create_application_builder()

# Configure the middleware pipeline
app_builder.configure_middleware(lambda builder: (
    builder
    .use_middleware(LoggingMiddleware)  # Built-in, assuming it's registered or takes a logger
    .use_middleware(CustomAuthMiddleware)
    .use_middleware(DummyFinalHandler) # Your actual request handler might be the last "middleware"
))

# Build the service provider
provider = app_builder.build()

# Get the configured middleware pipeline
# The pipeline itself is registered as a service
from wd.di.middleware import MiddlewarePipeline 
pipeline = provider.get_service(MiddlewarePipeline)

# --- Execute the pipeline ---
# import asyncio # Required if running top-level await

async def main():
    # Example 1: Authenticated request
    print("--- Running Authenticated Request ---")
    auth_context = RequestContext(path="/secret-data", is_authenticated=True)
    try:
        result_auth = await pipeline.execute(auth_context)
        print(f"Pipeline Result (Authenticated): {result_auth}")
    except Exception as e:
        print(f"Error (Authenticated): {e}")

    print("\\n--- Running Unauthenticated Request ---")
    # Example 2: Unauthenticated request
    unauth_context = RequestContext(path="/secret-data", is_authenticated=False)
    try:
        result_unauth = await pipeline.execute(unauth_context)
        print(f"Pipeline Result (Unauthenticated): {result_unauth}")
    except Exception as e:
        print(f"Error (Unauthenticated): {e}")

# To run this example:
# asyncio.run(main())
```

When `pipeline.execute(context)` is called, the `context` object flows through `LoggingMiddleware`, then `CustomAuthMiddleware`, and finally `DummyFinalHandler` (if authentication passes). The order of registration with `use_middleware` matters.

---

## Middleware Dependencies

Middleware components themselves can have dependencies, which will be resolved by the DI container when the middleware is created for the pipeline. This allows your middleware to use other services (e.g., a logging service, a configuration service).

The `MiddlewareBuilder` internally uses the `ServiceCollection` it was created with to build a temporary `ServiceProvider` to resolve middleware instances each time `pipeline.execute()` is called. This ensures middleware dependencies are resolved with the correct lifetimes (e.g., scoped dependencies for a scoped pipeline execution).

---

By leveraging the middleware pipeline, you can create clean, modular, and reusable components for handling tasks that span across multiple parts of your application. 
```

---

### 14. docs\roadmap.md

- **File ID**: file_13
- **Type**: File
- **Line Count**: 182
- **Description**: File at docs\roadmap.md

**Content**:
```
# WD-DI Library Roadmap

This document outlines the planned features and enhancements for the WD-DI library. It is based on the previous internal TODO list and will be updated as the project progresses.

---

### Planned Features and Enhancements

#### 1. Dependency Injection Container Enhancements

- [x] **Scoped Services Resolution & Scope Management**  
  *Explicit scope creation and disposal management for scoped services have been implemented.*

- [x] **Circular Dependency Detection**  
  *Detection of circular dependencies during resolution (with proper error messages) is now in place.*

- [ ] **Open Generic Types Support:**  
  Add the ability to register and resolve open generic types for generic service definitions.

- [x] **Instance Registration:**  
  *The `add_instance` API for registering pre-instantiated services has been implemented.*

- [ ] **Multiple Implementations / Named Services:**  
  Support multiple registrations for a single service type and allow resolution as collections.

- [ ] **Improved Constructor Injection:**  
  Enhance dependency resolution to handle default parameter values and cases with missing or ambiguous type annotations.

- [x] **Thread Safety Improvements:**  
  *Review and enhance the container to be thread-safe in multi-threaded environments.* (ContextVar for circular dependency stack implemented)

---

#### 2. Middleware Pipeline Enhancements

- [ ] **Exception Handling Integration:**  
  Integrate `ExceptionHandlerMiddleware` into the default pipeline configuration and add tests for graceful error handling.

- [ ] **Middleware Registration & Lifetime Management:**  
  Refine middleware registration to better manage middleware lifetimes and resolve dependencies within appropriate scopes.

- [ ] **Advanced Pipeline Configuration:**  
  Explore features like branching pipelines, conditional middleware execution, or pipeline termination.

---

#### 3. Options/Configuration Enhancements

- [ ] **Type Conversion and Validation:**  
  Improve the `OptionsBuilder` to support robust type conversion and integrate validation logic.

- [ ] **Dynamic Configuration Reloading:**  
  Optionally add support for reloading configuration when underlying sources (e.g., JSON or environment variables) change.

---

#### 4. Testing and Documentation

- [ ] **Expanded Test Coverage:**  
  Add tests for new and pending features (e.g., open generic types, multiple implementations).

- [ ] **Documentation and Code Comments:**  
  Enhance inline documentation, add usage examples, and update the README to guide users.

- [x] **Refactor Global State:**  
  *The global `services` instance has been removed. DI container setup now requires explicit `ServiceCollection` instantiation.*

---

#### 5. Additional Features

- [ ] **Integration with Python Logging:**  
  Replace default print statements in logging middleware with integration into Python's standard logging module.

- [ ] **Support for Async Service Factories:**  
  Investigate and add support for asynchronous factory methods for services requiring async initialization.

- [ ] **Dependency Injection Extensions:**  
  Create helper functions or decorators for common patterns (e.g., function injection, async injection) to extend the framework's usability.

---

## Future Ideas and Exploration

This section lists features and concepts that are under consideration for future development or as potential extensions to the library. These are not yet committed items but represent areas of interest.

(Note: Code snippets below are conceptual and assume `from wd.di import ServiceCollection` and `sc = create_service_collection()` are defined.)

1.  **Service Discovery and Assembly Scanning**
    *   Auto-registration of services based on decorators/attributes.
    *   Scanning assemblies/modules for services marked for registration.
    *   Convention-based registration (e.g., all classes ending with 'Service').

2.  **Advanced Service Resolution**
    *   **Named/Keyed Services:**
        ```python
        # sc.add_singleton(IService, ServiceA, name="serviceA")
        # sc.add_singleton(IService, ServiceB, name="serviceB")
        ```
    *   **Enumerable Resolution (Resolving all implementations of an interface):**
        ```python
        # @sc.singleton()
        # class Processor:
        #     def __init__(self, handlers: list[IHandler]): # Inject all IHandler implementations
        #         self.handlers = handlers
        ```
    *   **Lazy Resolution:**
        ```python
        # from wd.di import Lazy # Hypothetical Lazy type
        # @sc.singleton()
        # class Service:
        #     def __init__(self, lazy_dep: Lazy[ExpensiveService]):
        #         self._dep = lazy_dep  # ExpensiveService only created when self._dep.value is accessed
        ```

3.  **Enhanced Async Support**
    *   **Async Service Initialization/Factories:** (Covered in "Additional Features")
    *   **Async Disposal (`aclose` or `adispose`):** Support for services that need to perform asynchronous cleanup.
        ```python
        # @sc.scoped() # Or other lifetimes
        # class AsyncDisposableResource:
        #     async def setup(self):
        #         # async setup
        #         pass
        #     async def aclose(self): # Or async_dispose
        #         # async cleanup
        #         pass
        # # ServiceProvider scope would need to handle await scope.aclose()
        ```

4.  **Enhanced Configuration (beyond current `Options` pattern)**
    *   **Environment-Specific Configuration Files:** (Already conceptually manageable by how `Configuration` is built)
    *   **Binding to Nested Dataclasses:** (Already supported by current `Options` pattern and `Configuration` section binding)

5.  **Service Replacement and Decoration**
    *   **Replace Existing Registration:**
        ```python
        # sc.replace_singleton(IService, NewImplementation)
        ```
    *   **Decorate Existing Service:**
        ```python
        # sc.decorate(IService, lambda sp, service_instance: LoggingDecorator(service_instance, sp.get_service(ILogger)))
        ```

6.  **Enhanced Validation**
    *   **Startup Validation:** Extended checks during `build_service_provider()` for common issues.
        ```python
        # provider = sc.build_service_provider(validate_on_build=True) # Check for missing dependencies, certain circular refs
        ```
    *   **Scope Validation:** Ensure scoped services aren't inadvertently resolved by singletons in a problematic way.

7.  **Service Factory Enhancements**
    *   Support for factories that can take runtime parameters beyond just the `ServiceProvider`.
        ```python
        # # For services that need parameters not known at registration time
        # # This is more of an application-level factory pattern that DI can help construct.
        # sc.add_transient_factory(lambda sp, param1: MyServiceWithParams(sp.get_service(IDependency), param1))
        ```

8.  **Diagnostics and Debugging Tools**
    *   **Dependency Graph Visualization:** Tools or methods to inspect the resolved dependency tree.
    *   **Resolution Metrics:** Optional tracking of service creation times, instance counts, etc.

9.  **Middleware Enhancements (beyond current pipeline)**
    *   **Ordered Middleware:** (Already supported by registration order)
    *   **Conditional Middleware:** (Already possible by implementing logic within `invoke`)

10. **Scope Features**
    *   **Named Scopes:** (For scenarios requiring multiple distinct types of scopes)
    *   **Scope Events:** Callbacks for scope creation or disposal.

11. **Extended Type Support**
    *   **Generic Service Support:** (Covered in "Container Enhancements" - Open Generics)
    *   **Optional Dependencies:** Clear patterns for handling optional dependencies (e.g. `dep: IMyService | None = None`).

12. **Testing Utilities**
    *   **Test ServiceProvider/ServiceCollection Helpers:** Utilities to simplify mocking or overriding services in test environments.
        ```python
        # with sc.override_service(IMyService, MockMyService()):
        #    provider = sc.build_service_provider()
        #    # ... tests ...
        ``` 
```

---

### 15. docs\tutorial\01-domain.md

- **File ID**: file_14
- **Type**: File
- **Line Count**: 133
- **Description**: File at docs\tutorial\01-domain.md

**Content**:
```
## Design Tutorial: Building an Order Processing Application with WD-DI

In this tutorial, we'll build a small order processing application using WD-DI. This guide will demonstrate how to structure your application using dependency injection as the backbone of your architecture. By the end of this tutorial, you'll see how WD-DI helps you achieve separation of concerns, robust configuration management, and a modular, testable codebase.

---

## Tutorial Introduction

Dependency injection is a cornerstone of modern software architecture. It enables you to build loosely coupled, maintainable, and testable systems by decoupling the creation of objects from their usage. In this tutorial, we'll use WD-DI to build an Order Processing application that demonstrates:

- **Separation of concerns** via layered architecture.
- **Interface-driven design** to allow for flexibility and easy testing.
- **Robust configuration management** using strongly-typed options.
- **Middleware pipelines** for cross-cutting concerns (optional extension).
- **Proper management of service lifetimes** (transient, singleton, and scoped).

---

## Application Overview

Our sample application, **OrderProcessor**, will:

- Accept and process an order.
- Validate and save the order.
- Notify the user via email.
- Log key actions throughout the process.

---

## Project Structure

For clarity, our project is organized as follows. This tutorial series will guide you through creating the components within these conceptual directories.

```
order_processor/
├── main.py                 # Application entry point (covered in Part 3)
├── domain/                 # (Covered in this Part - 01-domain.md)
│   ├── models.py           # Domain models (e.g., Order)
│   └── interfaces.py       # Domain interfaces (e.g., IOrderService)
├── data/                   # (Covered in Part 2 - 02-services.md)
│   └── repository.py       # Data access implementation
├── services/               # (Covered in Part 2 - 02-services.md)
│   └── order_service.py    # Business logic implementation
├── presentation/           # (Covered in Part 3 - 03-wiring.md)
│   └── controller.py       # Application controller (simulated CLI)
└── infrastructure/         # (Covered in Part 2 - 02-services.md)
    ├── config.py           # Configuration classes
    └── logging_service.py  # Logging service implementation
```

Note: The original `_old_docs/design_tutorial.md` file from which this structure is adapted will be removed as its content is fully migrated.

---

# Tutorial - Step 1: Domain and Project Structure

Setting up the domain models and project layout for the order processing application. 

# Tutorial Part 1: Domain Layer

In our Order Processing application, the Domain Layer defines the core business entities and the contracts (interfaces) for how these entities are handled. It should be independent of specific data storage mechanisms or business logic implementations.

## Key Components

*   **Models:** Dataclasses or simple classes representing your business entities.
*   **Interfaces:** Abstract Base Classes (ABCs) defining the expected operations for services and repositories that will interact with these models.

---

## Defining the Order Model

First, let's define our primary business entity, the `Order`.

**File: `domain/models.py`** (Conceptual path for the tutorial)

```python
from dataclasses import dataclass

@dataclass
class Order:
    order_id: str
    item: str
    quantity: int
    price: float
    # You could add customer_id, status, created_at, etc.
```

This simple dataclass will hold information about an order.

---

## Defining Domain Interfaces

Next, we define the interfaces for services that will operate on our domain models. These interfaces will be implemented by other layers (like the Data Access Layer or Service Layer).

**File: `domain/interfaces.py`** (Conceptual path for the tutorial)

```python
from abc import ABC, abstractmethod
from .models import Order # Assuming models.py is in the same conceptual directory

class IOrderRepository(ABC):
    """Interface for data persistence operations related to Orders."""
    @abstractmethod
    def save_order(self, order: Order):
        pass

    @abstractmethod
    def get_order_by_id(self, order_id: str) -> Order | None:
        pass

class IOrderService(ABC):
    """Interface for business logic related to processing Orders."""
    @abstractmethod
    def process_new_order(self, order: Order) -> bool:
        """Processes a new order and returns True if successful."""
        pass

class ILogger(ABC):
    """A generic logger interface for infrastructure concerns."""
    @abstractmethod
    def log_info(self, message: str):
        pass

    @abstractmethod
    def log_error(self, message: str, exception: Exception | None = None):
        pass

```

In this step, we've laid the groundwork by defining what our application deals with (`Order`) and what operations we expect to perform (`IOrderRepository`, `IOrderService`, and a utility `ILogger`). These interfaces ensure that our business logic (which will use `IOrderService`) and data access (which will implement `IOrderRepository`) are decoupled.

In the next part, we'll look at implementing these interfaces. 
```

---

### 16. docs\tutorial\02-services.md

- **File ID**: file_15
- **Type**: File
- **Line Count**: 146
- **Description**: File at docs\tutorial\02-services.md

**Content**:
```
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
```

---

### 17. docs\tutorial\03-wiring.md

- **File ID**: file_16
- **Type**: File
- **Line Count**: 266
- **Description**: File at docs\tutorial\03-wiring.md

**Content**:
```
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

```

---

## Summary

- **Total Files**: 17
- **Code Files**: 0
- **Regular Files**: 17
- **Total Lines of Code**: 2689
