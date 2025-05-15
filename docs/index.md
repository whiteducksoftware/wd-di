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