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