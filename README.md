# WD-DI: .NET Style Dependency Injection for Python 🐍


[![PyPI version](https://badge.fury.io/py/wd-di.svg)](https://badge.fury.io/py/wd-di)
[![Build Status](https://github.com/whiteducksoftware/wd-di/actions/workflows/deploy-whiteduck-pypi.yml/badge.svg)](https://github.com/whiteducksoftware/wd-di/actions)


WD-DI brings the robust and flexible dependency injection patterns of .NET to your Python applications, with no external library dependencies—just Python's standard library. ✨

**Full documentation can be found at [https://whiteducksoftware.github.io/wd-di/](https://whiteducksoftware.github.io/wd-di/) (or in the `/docs` directory).** 📚

> For beginners, the **[Core Concepts](docs/core-concepts/index.md)** and **[Tutorials](docs/tutorial/index.md)** sections in the documentation are a great place to start to understand not just *how* to use DI, but *why* it's beneficial!

---

## Why WD-DI? 🤔

*   **Simplified Dependency Management:** Effortlessly manage object creation and lifecycles.
*   **Enhanced Testability:** Easily mock dependencies for robust unit tests. 🧪
*   **Modular Architecture:** Build loosely coupled, maintainable, and scalable applications. 🧩
*   **Familiar Patterns:** Leverage .NET-inspired DI concepts like [service lifetimes (Singleton, Scoped, Transient)](docs/core-concepts/lifetimes.md), [constructor injection](docs/core-concepts/constructor-injection.md), and the [Options pattern for configuration](docs/core-concepts/configuration.md).
*   **Pythonic and Lightweight:** Clean, intuitive API that integrates smoothly into your Python projects. 🐍

---

## Installation 📦

```bash
pip install wd-di
```

---

## Quick Example: The Power of WD-DI 🚀

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

Dive into the **[full documentation](https://whiteducksoftware.github.io/wd-di/)** to explore service lifetimes, configuration, middleware, and more! 📖

---

## Contributing 🤝

Contributions are welcome! Please see the main documentation site for details on how to contribute, report issues, or request features.

---

## License 📜

This project is licensed under the terms of the LICENSE file included in the repository.