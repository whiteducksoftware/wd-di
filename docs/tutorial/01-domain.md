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