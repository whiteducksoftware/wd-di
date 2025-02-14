# Design Guide and Tutorial

Looking at numerous Python repositories, one thing is clear: the gap between good and terrible code is more pronounced in Python than in any other language. In no other language will you find highly-downloaded libraries with such questionable software design decisions and architecture.

Python is a flexible language, and everyone should embrace this flexibility. However, flexibility should not be an excuse for avoiding clean and structured architecture, because there comes a point in every developer's life when they become overwhelmed by their own library and the past decisions they made.

This is an attempt to increase awareness of dependency injection - specifically the way we prefer to use it (the .NET style) and how we implement it when building real software. Dependency injection is an often neglected topic, which is reason enough for us to show you the amazing things it enables you to do.

WD-DI isn't just a tool for resolving dependencies—it's a foundation for designing well-structured applications. Follow these guidelines and examples to leverage dependency injection in your project.

The first part explains the theory behind the DI pattern, while the second part implements a small application built on these principles!

By following this design guide, you can use WD-DI as the backbone for a well-architected, modular, and testable software system. Embrace dependency injection to:

- **Decouple components** using constructor injection.
- **Implement interface-driven design** for flexible, swappable components.
- **Centralize cross-cutting concerns** with a middleware pipeline.
- **Manage configurations** via strongly-typed options.
- **Enhance testability** by isolating dependencies and using mocks.
- **Build layered architectures** that scale and evolve gracefully.

This guide, with its accompanying code examples, provides a roadmap for integrating WD-DI into your projects, ensuring that your architecture remains robust, maintainable, and adaptable over time.

## Design Guide: Architecting Your Software with WD-DI

### 1. Separation of Concerns

**Principle:**  
Break your application into components with clear responsibilities. Use constructor injection to make dependencies explicit and decouple components.

**Example:**

```python
# EmailService: A service responsible for sending emails
class EmailService:
    def send_email(self, recipient: str, subject: str, body: str):
        print(f"Sending email to {recipient}")

# UserService: Depends on EmailService for notifications
@singleton()
class UserService:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    def notify(self, user_id: str, message: str):
        # In a real app, fetch user's email from a repository, etc.
        self.email_service.send_email("user@example.com", "Notification", message)

# Register and use the services:
services.add_singleton(EmailService)
services.add_singleton(UserService)

provider = services.build_service_provider()
user_service = provider.get_service(UserService)
user_service.notify("123", "Your order has shipped!")
```

**When to use:**  
Apply separation of concerns to keep business logic distinct from infrastructure (e.g., sending emails, logging), making your code easier to maintain and test.

---

### 2. Component-Based Design

**Interface-Driven Development**

**Principle:**  
Define interfaces (or abstract base classes) and register implementations against these interfaces. This allows you to swap implementations and write cleaner tests.

**Example:**

```python
from abc import ABC, abstractmethod

# Define an interface for user repository
class IUserRepository(ABC):
    @abstractmethod
    def get_user(self, user_id: str):
        pass

# Implementation of the repository interface
@singleton()
class UserRepository(IUserRepository):
    def get_user(self, user_id: str):
        return {"id": user_id, "name": "John Doe"}

# Register the interface and its implementation:
services.add_singleton(IUserRepository, UserRepository)
```

**Lifetimes Matter**

**Principle:**  
Select service lifetimes based on the nature of the dependency:
- **Transient:** New instance per request.
- **Singleton:** One instance for the entire application.
- **Scoped:** One instance per defined scope (e.g., per web request).

**Example:**

```python
# Transient: A new instance is created each time
services.add_transient(IService, ServiceImpl)

# Singleton: One instance is shared application-wide
services.add_singleton(IService, ServiceImpl)

# Scoped: One instance per explicit scope
services.add_scoped(IService, ServiceImpl)
```

**When to use:**  
Use interface-driven design to enhance flexibility and testing. Choose lifetimes based on resource usage and desired sharing.

---

### 3. Middleware for Cross-Cutting Concerns

**Principle:**  
Centralize and modularize common tasks (logging, authentication, error handling) using a middleware pipeline.

**Example:**

```python
from wd.di.middleware import IMiddleware

# A simple logging middleware that wraps request processing
class LoggingMiddleware(IMiddleware):
    async def invoke(self, context, next):
        print("Request started")
        result = await next()
        print("Request finished")
        return result

# Configure the middleware pipeline:
app = services.create_application_builder()
app.configure_middleware(lambda builder: (
    builder.use_middleware(LoggingMiddleware)
))
provider = app.build()
pipeline = provider.get_service(MiddlewarePipeline)

# Simulated context for demonstration:
class DummyContext:
    is_authenticated = True

import asyncio
async def run_pipeline():
    result = await pipeline.execute(DummyContext())
    return result

asyncio.run(run_pipeline())
```

**When to use:**  
Utilize middleware for tasks that apply to many or all requests, ensuring consistency and reducing redundancy.

---

### 4. Robust Configuration Management

**Principle:**  
Centralize configuration using strongly-typed options. This provides compile-time checks and clearer configuration structures.

**Example:**

```python
from dataclasses import dataclass
from wd.di.config import Configuration, Options

@dataclass
class AppConfig:
    debug: bool = False
    api_key: str = ""

# Create and register configuration
config = Configuration({
    "app": {
        "debug": True,
        "apiKey": "secret-key"
    }
})

services.add_singleton_factory(IConfiguration, lambda _: config)
services.configure(AppConfig, section="app")

# Example service that uses configuration:
@singleton()
class AppService:
    def __init__(self, options: Options[AppConfig]):
        self.config = options.value

    def run(self):
        if self.config.debug:
            print("Running in debug mode")
        else:
            print("Running in production mode")

provider = services.build_service_provider()
app_service = provider.get_service(AppService)
app_service.run()
```

**When to use:**  
Adopt strongly-typed configuration to centralize and validate settings, reducing errors and simplifying environment-specific configuration.

---

### 5. Enhancing Testability and Maintainability

**Principle:**  
Using DI improves testability by allowing easy injection of mocks or stubs. Constructor injection makes dependencies explicit and testing straightforward.

**Example:**

```python
# A mock version of EmailService for testing purposes
class MockEmailService:
    def send_email(self, recipient, subject, body):
        print("Mock email sent")

# Testing UserService with a mock dependency:
def test_user_service():
    # Inject the mock email service directly
    user_service = UserService(email_service=MockEmailService())
    user_service.notify("123", "Test Message")

test_user_service()
```

**When to use:**  
Enhance testability by isolating components and substituting real implementations with mocks during unit tests.

---

### 6. Evolving Architecture with WD-DI

**Layered Application Architecture**

**Principle:**  
Structure your application into layers (Domain, Data Access, Presentation, Infrastructure) and use DI to manage dependencies between layers.

**Example:**

**Domain Layer:**

```python
from abc import ABC, abstractmethod

class IOrderService(ABC):
    @abstractmethod
    def process_order(self, order_id: str):
        pass

@singleton()
class OrderService(IOrderService):
    def process_order(self, order_id: str):
        print(f"Processing order {order_id}")
```

**Data Access Layer:**

```python
class IOrderRepository(ABC):
    @abstractmethod
    def get_order(self, order_id: str):
        pass

@singleton()
class OrderRepository(IOrderRepository):
    def get_order(self, order_id: str):
        return {"id": order_id, "item": "Book"}
```

**Presentation Layer:**

```python
@transient()
class OrderController:
    def __init__(self, order_service: IOrderService):
        self.order_service = order_service

    def handle_order(self, order_id: str):
        self.order_service.process_order(order_id)
```

**Infrastructure Layer:**

```python
# External logging service via instance registration
class Logger:
    def log(self, msg: str):
        print(f"LOG: {msg}")

logger_instance = Logger()
services.add_instance(Logger, logger_instance)
```

**Assembling the Application:**

```python
# Register layers with the DI container:
services.add_singleton(IOrderService, OrderService)
services.add_singleton(IOrderRepository, OrderRepository)
services.add_transient(OrderController)

provider = services.build_service_provider()
controller = provider.get_service(OrderController)
controller.handle_order("order123")
```

**When to use:**  
Build a layered architecture using WD-DI to cleanly separate business logic, data access, presentation, and infrastructure concerns. This enhances maintainability and scalability.

---

### 7. Practical Advice for Evolving Architectures

**Start Simple, Then Expand**

**Principle:**  
Begin with a minimal DI setup. As your project grows, add more sophisticated registration, resolution, and middleware configurations.

**Example:**

```python
# Start by registering core services:
services.add_singleton(DatabaseService)
services.add_singleton(UserService)

# Later, as the project evolves, integrate additional layers and middleware:
app = services.create_application_builder()
app.configure_middleware(lambda builder: (
    builder.use_middleware(LoggingMiddleware)
))
```

**When to use:**  
Adopt an incremental approach. Begin with essential services and progressively integrate advanced patterns like middleware pipelines, dynamic configuration, and custom lifetime management.



### 8. Common Python Anti-Patterns and DI Solutions

**Principle:**  
Python's flexibility, while powerful, can lead to common architectural pitfalls. Using dependency injection helps avoid these anti-patterns and promotes maintainable code.

#### Global State and Singletons

**Anti-Pattern:**
```python
# global_config.py
class GlobalConfig:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.api_key = "secret"
        self.debug = True

# Used everywhere in the codebase:
config = GlobalConfig.get_instance()
```

**DI Solution:**
```python
from dataclasses import dataclass
from wd.di.config import Configuration, Options

@dataclass
class AppConfig:
    api_key: str
    debug: bool

@singleton()
class ConfiguredService:
    def __init__(self, options: Options[AppConfig]):
        self.config = options.value
    
    def do_something(self):
        if self.config.debug:
            print("Debug mode")

# Register in your DI container
services.configure(AppConfig, section="app")
services.add_singleton(ConfiguredService)
```

#### Hidden Dependencies and Import-Time Side Effects

**Anti-Pattern:**
```python
# database.py
import sqlite3

# Global connection created at import time
db = sqlite3.connect("app.db")

class UserRepository:
    def get_user(self, user_id):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

# Used elsewhere:
repo = UserRepository()
user = repo.get_user(123)
```

**DI Solution:**
```python
from abc import ABC, abstractmethod
import sqlite3

class IDatabase(ABC):
    @abstractmethod
    def execute(self, query: str, params: tuple):
        pass

@singleton()
class Database(IDatabase):
    def __init__(self, connection_string: str):
        self.connection = sqlite3.connect(connection_string)
    
    def execute(self, query: str, params: tuple):
        cursor = self.connection.cursor()
        return cursor.execute(query, params)

@singleton()
class UserRepository:
    def __init__(self, db: IDatabase):
        self.db = db
    
    def get_user(self, user_id):
        return self.db.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# Register with DI:
services.add_singleton(IDatabase, Database, connection_string="app.db")
services.add_singleton(UserRepository)
```

#### Module-Level Logic and Circular Dependencies

**Anti-Pattern:**
```python
# user_service.py
from order_service import get_user_orders

def get_user_details(user_id):
    orders = get_user_orders(user_id)
    return {"id": user_id, "orders": orders}

# order_service.py
from user_service import get_user_details

def get_user_orders(user_id):
    user = get_user_details(user_id)  # Circular dependency!
    return [{"order_id": 1}]
```

**DI Solution:**
```python
from abc import ABC, abstractmethod

class IOrderService(ABC):
    @abstractmethod
    def get_user_orders(self, user_id: str) -> list:
        pass

class IUserService(ABC):
    @abstractmethod
    def get_user_details(self, user_id: str) -> dict:
        pass

@singleton()
class OrderService(IOrderService):
    def get_user_orders(self, user_id: str) -> list:
        return [{"order_id": 1}]

@singleton()
class UserService(IUserService):
    def __init__(self, order_service: IOrderService):
        self.order_service = order_service
    
    def get_user_details(self, user_id: str) -> dict:
        orders = self.order_service.get_user_orders(user_id)
        return {"id": user_id, "orders": orders}

# Register with DI:
services.add_singleton(IOrderService, OrderService)
services.add_singleton(IUserService, UserService)
```

#### Monolithic Classes with Mixed Responsibilities

**Anti-Pattern:**
```python
class UserManager:
    def __init__(self):
        self.db = sqlite3.connect("app.db")
        self.logger = logging.getLogger()
        self.mailer = smtplib.SMTP("smtp.example.com")
    
    def create_user(self, email, password):
        self.logger.info(f"Creating user: {email}")
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                      (email, password))
        self.db.commit()
        
        self.mailer.sendmail(
            "system@example.com",
            email,
            "Welcome to our service!"
        )
```

**DI Solution:**
```python
@singleton()
class UserRepository:
    def __init__(self, db: IDatabase):
        self.db = db
    
    def create_user(self, email: str, password: str):
        self.db.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, password)
        )

@singleton()
class EmailService:
    def __init__(self, smtp_config: Options[SmtpConfig]):
        self.config = smtp_config.value
    
    def send_welcome_email(self, email: str):
        # Email sending logic here
        pass

@singleton()
class UserService:
    def __init__(
        self,
        repository: UserRepository,
        email_service: EmailService,
        logger: ILogger
    ):
        self.repository = repository
        self.email_service = email_service
        self.logger = logger
    
    def create_user(self, email: str, password: str):
        self.logger.info(f"Creating user: {email}")
        self.repository.create_user(email, password)
        self.email_service.send_welcome_email(email)
```

#### Static Methods and Utility Classes

**Anti-Pattern:**
```python
class PaymentUtils:
    @staticmethod
    def calculate_tax(amount):
        return amount * 0.2
    
    @staticmethod
    def validate_credit_card(number):
        return len(number) == 16

class OrderProcessor:
    def process_payment(self, amount, card_number):
        if PaymentUtils.validate_credit_card(card_number):
            total = amount + PaymentUtils.calculate_tax(amount)
            # Process payment...
```

**DI Solution:**
```python
class ITaxCalculator(ABC):
    @abstractmethod
    def calculate_tax(self, amount: float) -> float:
        pass

class IPaymentValidator(ABC):
    @abstractmethod
    def validate_credit_card(self, number: str) -> bool:
        pass

@singleton()
class DefaultTaxCalculator(ITaxCalculator):
    def calculate_tax(self, amount: float) -> float:
        return amount * 0.2

@singleton()
class DefaultPaymentValidator(IPaymentValidator):
    def validate_credit_card(self, number: str) -> bool:
        return len(number) == 16

@singleton()
class OrderProcessor:
    def __init__(
        self,
        tax_calculator: ITaxCalculator,
        payment_validator: IPaymentValidator
    ):
        self.tax_calculator = tax_calculator
        self.payment_validator = payment_validator
    
    def process_payment(self, amount: float, card_number: str):
        if self.payment_validator.validate_credit_card(card_number):
            total = amount + self.tax_calculator.calculate_tax(amount)
            # Process payment...
```

**When to use:**
Apply these patterns when:
- You need to replace implementations for testing
- Your application configuration needs to change based on environment
- You want to avoid tight coupling between modules
- You need to manage complex object lifecycles
- You want to make dependencies explicit and traceable

---

## Design Tutorial: Building an Order Processing Application with WD-DI

In this tutorial, we'll build a small order processing application using WD-DI. This guide will demonstrate how to structure your application using dependency injection as the backbone of your architecture. By the end of this tutorial, you'll see how WD-DI helps you achieve separation of concerns, robust configuration management, and a modular, testable codebase.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Application Overview](#application-overview)
3. [Project Structure](#project-structure)
4. [Architectural Layers and Design](#architectural-layers-and-design)
    - [Domain Layer](#domain-layer)
    - [Data Access Layer](#data-access-layer)
    - [Service Layer (Business Logic)](#service-layer-business-logic)
    - [Presentation Layer](#presentation-layer)
    - [Infrastructure Layer](#infrastructure-layer)
5. [Wiring It All Up with WD-DI](#wiring-it-all-up-with-wd-di)
6. [Running the Application](#running-the-application)
7. [Conclusion](#conclusion)

---

## 1. Introduction

Dependency injection is a cornerstone of modern software architecture. It enables you to build loosely coupled, maintainable, and testable systems by decoupling the creation of objects from their usage. In this tutorial, we'll use WD-DI to build an Order Processing application that demonstrates:

- **Separation of concerns** via layered architecture.
- **Interface-driven design** to allow for flexibility and easy testing.
- **Robust configuration management** using strongly-typed options.
- **Middleware pipelines** for cross-cutting concerns (optional extension).
- **Proper management of service lifetimes** (transient, singleton, and scoped).

---

## 2. Application Overview

Our sample application, **OrderProcessor**, will:

- Accept and process an order.
- Validate and save the order.
- Notify the user via email.
- Log key actions throughout the process.

---

## 3. Project Structure

For clarity, our project is organized as follows:

```
order_processor/
├── design_tutorial.md      # This tutorial file
├── main.py                 # Application entry point
├── domain/
│   ├── models.py           # Domain models (e.g., Order)
│   └── interfaces.py       # Domain interfaces (e.g., IOrderService)
├── data/
│   └── repository.py       # Data access implementation
├── services/
│   └── order_service.py    # Business logic implementation
├── presentation/
│   └── controller.py       # Application controller (simulated CLI)
└── infrastructure/
    ├── config.py           # Configuration classes
    └── logging_service.py  # Logging service implementation
```

---

## 4. Architectural Layers and Design

### Domain Layer

This layer defines your core business entities and contracts.

**File: `domain/models.py`**

```python
from dataclasses import dataclass

@dataclass
class Order:
    order_id: str
    item: str
    quantity: int
    price: float
```

**File: `domain/interfaces.py`**

```python
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

### Data Access Layer

Handles persistence and data operations.

**File: `data/repository.py`**

```python
from domain.interfaces import IOrderRepository

class OrderRepository(IOrderRepository):
    def __init__(self, logger):
        self.logger = logger

    def save_order(self, order):
        self.logger.log(f"Order saved: {order.order_id}")
        # In a real application, implement database save logic here.
```

---

### Service Layer (Business Logic)

Encapsulates your core business rules.

**File: `services/order_service.py`**

```python
from domain.interfaces import IOrderService, IOrderRepository
from domain.models import Order

class OrderService(IOrderService):
    def __init__(self, repository: IOrderRepository, logger):
        self.repository = repository
        self.logger = logger

    def process_order(self, order: Order):
        self.logger.log(f"Processing order: {order.order_id}")
        # Business logic: validate order, process payment, etc.
        self.repository.save_order(order)
        self.logger.log(f"Order processed: {order.order_id}")
```

---

### Presentation Layer

Provides the interface to interact with your application (e.g., a CLI or web controller).

**File: `presentation/controller.py`**

```python
from domain.models import Order

class OrderController:
    def __init__(self, order_service):
        self.order_service = order_service

    def submit_order(self, order_id, item, quantity, price):
        order = Order(order_id=order_id, item=item, quantity=quantity, price=price)
        self.order_service.process_order(order)
```

---

### Infrastructure Layer

Manages cross-cutting concerns like configuration and logging.

**File: `infrastructure/config.py`**

```python
from dataclasses import dataclass

@dataclass
class AppConfig:
    debug: bool = False
    email_server: str = ""
```

**File: `infrastructure/logging_service.py`**

```python
class Logger:
    def log(self, message: str):
        print(f"[LOG]: {message}")
```

---

## 5. Wiring It All Up with WD-DI

Now we'll integrate everything using WD-DI. The following code in `main.py` demonstrates how to register your services and build the application.

**File: `main.py`**

```python
from wd.di import services
from wd.di.config import Configuration, Options
from infrastructure.config import AppConfig
from infrastructure.logging_service import Logger
from data.repository import OrderRepository
from services.order_service import OrderService
from presentation.controller import OrderController

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
services.add_singleton(OrderRepository)

# Register business logic (order service)
services.add_singleton(OrderService)

# Register presentation layer (controller)
services.add_transient(OrderController)

# Build the service provider
provider = services.build_service_provider()

# Resolve the controller and simulate an order submission
controller = provider.get_service(OrderController)
controller.submit_order("order001", "Widget", 5, 19.99)
```

---

## 6. Running the Application

To run the application, execute the following command from your terminal:

```bash
python main.py
```

You should see log messages indicating each step of the order processing workflow, such as order submission, processing, and saving.

---

## 7. Conclusion

In this tutorial, we've built a simple order processing application that demonstrates how to:

- **Separate concerns** by splitting the application into distinct layers.
- **Design using interfaces** and concrete implementations to achieve a flexible, testable codebase.
- **Manage configuration** through strongly-typed options.
- **Leverage WD-DI** to wire all components together, ensuring proper management of service lifetimes and dependencies.

By using WD-DI, you not only simplify dependency management but also establish a solid foundation for building scalable and maintainable applications. This design tutorial shows that dependency injection is far more than a theoretical concept—it’s a practical tool for crafting high-quality software architectures.

