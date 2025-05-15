# Order Processor Example

This example demonstrates the use of `wd-di` to structure a simple order processing application following a layered architecture. It showcases how dependency injection can help in decoupling components, managing dependencies, and improving the testability and maintainability of an application.

## Scenario

The application simulates a basic order processing flow where an `OrderController` receives order details and uses an `IOrderService` to process the order. The `IOrderService` in turn relies on an `IOrderRepository` to persist order data. Additional services like configuration (`AppConfig`) and logging (`Logger`) are also utilized.

## Key Concepts Demonstrated

*   **Layered Architecture**: The example is structured into common application layers:
    *   `domain`: Contains business entities and interfaces (e.g., `IOrderRepository`, `IOrderService`).
    *   `data`: Contains data access implementations (e.g., `OrderRepository`).
    *   `services`: Contains business logic implementations (e.g., `OrderService`).
    *   `infrastructure`: Contains cross-cutting concerns like logging and configuration models (e.g., `Logger`, `AppConfig`).
    *   `presentation`: Contains components responsible for user interaction or API handling (e.g., `OrderController`).
*   **Dependency Injection Across Layers**: Each layer receives its dependencies via constructor injection, managed by the `wd-di` container.
    *   `OrderController` depends on `IOrderService`.
    *   `OrderService` depends on `IOrderRepository` and `Logger`.
    *   `OrderRepository` might depend on configuration or other infrastructure (though simplified in this example).
*   **Configuration Management**: 
    *   `IConfiguration` is registered to provide raw configuration data.
    *   `services.configure(AppConfig, section="app")` is used to bind a section of the configuration to a strongly-typed `AppConfig` object, which can then be injected into services.
*   **Service Lifetimes**: Different lifetimes are used for different services:
    *   `IConfiguration` and `IOrderRepository`, `IOrderService` are registered as **singletons**.
    *   `Logger` is registered as a pre-built **instance** (effectively a singleton).
    *   `OrderController` is registered as **transient**, meaning a new instance is created each time it's requested.
*   **Decoupling**: Components depend on abstractions (interfaces like `IOrderService`) rather than concrete implementations, allowing for easier substitution of implementations (e.g., for testing or different environments).

## Files and Structure

*   `main.py`: The main entry point of the application. It initializes the `ServiceCollection`, registers all services and their dependencies, builds the `ServiceProvider`, and then simulates an order submission by resolving and using the `OrderController`.
*   `domain/`: 
    *   `interfaces.py`: Defines abstract interfaces like `IOrderRepository` and `IOrderService`.
    *   (Potentially other files for domain entities if the example were more complex).
*   `data/`: 
    *   `repository.py`: Contains the `OrderRepository` class, implementing `IOrderRepository` for data persistence (likely using in-memory storage for this example).
*   `services/`: 
    *   `order_service.py`: Contains the `OrderService` class, implementing `IOrderService` and orchestrating the business logic for order processing.
*   `infrastructure/`: 
    *   `config.py`: Defines the `AppConfig` data class for application settings.
    *   `logging_service.py`: Defines a simple `Logger` class.
*   `presentation/`: 
    *   `controller.py`: Contains the `OrderController` class, responsible for handling incoming order requests (simulated) and interacting with the `IOrderService`.

## How it Works

1.  **Setup (`main.py`)**:
    *   A `ServiceCollection` is created.
    *   Application configuration is set up using `IConfiguration` and the `services.configure()` method to bind to the `AppConfig` class.
    *   Various services from different layers are registered with appropriate lifetimes (e.g., `Logger` as an instance, `OrderRepository` and `OrderService` as singletons, `OrderController` as transient).
    *   The `ServiceProvider` is built from the `ServiceCollection`.

2.  **Execution (`main.py`)**:
    *   An `OrderController` instance is resolved from the `ServiceProvider`.
    *   When the `OrderController` is created, `wd-di` injects an instance of `IOrderService` (which is `OrderService`).
    *   Similarly, when `OrderService` is created, `wd-di` injects instances of `IOrderRepository` (which is `OrderRepository`) and `Logger`.
    *   The `controller.submit_order(...)` method is called, triggering the order processing logic through the injected services.

## Running the Example

Navigate to the `examples/order_processor` directory and run:

```bash
python main.py
```

The output will likely show log messages from the `Logger` and any print statements within the services, indicating the flow of the order processing. For example:

```
Logger: INFO - Processing order: order001
OrderRepository: INFO - Saving order: order001, Item: Widget, Quantity: 5, Price: 19.99
OrderService: INFO - Order order001 processed successfully.
```
*(Note: Actual output depends on the print/log statements within the example's service implementations.)*

This example illustrates how `wd-di` facilitates building well-structured applications by managing dependencies and promoting loose coupling between different parts of your system. 