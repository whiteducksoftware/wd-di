<h1 align="center">WD-DI</h1>
<h2 align="center">.NET Style Dependency Injection for Python</h2>
<p align="center">
  <a href="https://pypi.org/project/wd-di/" target="_blank"><img alt="PyPI Version" src="https://img.shields.io/pypi/v/wd-di?style=for-the-badge&logo=pypi&label=pip%20version"></a>
  <img alt="Python Version" src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python">
  <a href="https://github.com/whiteducksoftware/wd-di/actions/workflows/deploy-whiteduck-pypi.yml" target="_blank"><img alt="CI Status" src="https://img.shields.io/github/actions/workflow/status/whiteducksoftware/wd-di/deploy-whiteduck-pypi.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white"></a>
  <a href="https://github.com/whiteducksoftware/wd-di/blob/main/LICENSE" target="_blank"><img alt="License" src="https://img.shields.io/pypi/l/wd-di?style=for-the-badge"></a>
  <a href="https://whiteduck.de" target="_blank"><img alt="Built by white duck" src="https://img.shields.io/badge/Built%20by-white%20duck%20GmbH-white?style=for-the-badge&labelColor=black"></a>
  <a href="https://www.linkedin.com/company/whiteduck" target="_blank"><img alt="LinkedIn" src="https://img.shields.io/badge/linkedin-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white&label=whiteduck"></a>
<a href="https://bsky.app/profile/whiteduck-gmbh.bsky.social" target="_blank"><img alt="Bluesky" src="https://img.shields.io/badge/bluesky-Follow-blue?style=for-the-badge&logo=bluesky&logoColor=%23fff&color=%23333&labelColor=%230285FF&label=whiteduck-gmbh"></a>
</p>

WD-DI brings the robust and flexible dependency injection patterns of .NET to your Python applications, with no external library dependencies, just Python's standard library.

**Full documentation can be found at [https://whiteducksoftware.github.io/wd-di/](https://whiteducksoftware.github.io/wd-di/) (or in the `/docs` directory).** 

> For beginners, the **[Core Concepts](https://whiteducksoftware.github.io/wd-di/core-concepts/)** and **[Tutorials](https://whiteducksoftware.github.io/wd-di/tutorial/)** sections in the documentation are a great place to start to understand not just *how* to use DI, but *why* it's beneficial!

---

## Why WD-DI? 🤔

*   **Simplified Dependency Management:** Effortlessly manage object creation and lifecycles.
*   **Enhanced Testability:** Easily mock dependencies for robust unit tests.
*   **Modular Architecture:** Build loosely coupled, maintainable, and scalable applications.
*   **Familiar Patterns:** Leverage .NET-inspired DI concepts like [service lifetimes (Singleton, Scoped, Transient)](https://whiteducksoftware.github.io/wd-di/core-concepts/lifetimes/), [constructor injection](https://whiteducksoftware.github.io/wd-di/core-concepts/constructor-injection/), and the [Options pattern for configuration](https://whiteducksoftware.github.io/wd-di/core-concepts/configuration/).
*   **Pythonic and Lightweight:** Clean, intuitive API that integrates smoothly into your Python projects.

| ✅ Feature | WD-DI | Typical alternatives |
|-----------|-------|----------------------|
| **Pure-stdlib** (zero runtime deps) | ✔ | ✘ pull in pydantic / C-extensions |
| **.NET-style lifetimes**<br>Transient • Singleton • **Scoped** (+ auto-dispose) | ✔ | ✘ Scoped rarely supported |
| **Strongly-typed Options binding** from dict/JSON/env → dataclass | ✔ | ✘ Dicts or manual parsing |
| **Decorator Pattern**	Built-in "wrap this service with that decorator" API? | ✔ | ✘ Only by manual implementation |
| **Middleware pipeline** bundled & DI-aware (async-first) | ✔ |✘ None ship a generic pipeline |
| **Decorator-based registration tied to *your* `ServiceCollection`** (no globals) | ✔ | ✘ Global singletons or meta-classes |
| **Thread-safe circular-dependency detection** via `ContextVar` | ✔ | ✘ Simple set → race-prone |
| **Full IDE type inference** for `get_service()` | ✔ | ✘ Returns `Any` / needs `cast()` |
| **Lean & readable** (~1.4 k LOC + robust test suite) | ✔ | ✘ wtf am I reading |

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

services = ServiceCollection()

# Define interfaces and implementations
class IEmailService:
    def send_email(self, to: str, subject: str, body: str) -> None:
        pass

class EmailService(IEmailService):
    def send_email(self, to: str, subject: str, body: str) -> None:
        print(f"\nSending email to {to}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print("Email sent successfully\n")

# UserService depends on IEmailService
class UserService:
    def __init__(self, email_service: IEmailService):
        self.email_service = email_service

    def notify_user(self, user_id: str, message: str) -> None:
        self.email_service.send_email(f"user{user_id}@example.com", "Notification", message)

# Register services
services.add_singleton(IEmailService, EmailService)
services.add_singleton(UserService)

# Build provider
# Services will be resolved and injected into services 
# like EmailService into UserService
provider = services.build_service_provider()

# Get services with proper type hints
email_service = provider.get_service(IEmailService)
user_service = provider.get_service(UserService)

# IDE will provide code completion for these methods
# No need to cast or use Any
email_service.send_email("test@example.com", "Test", "Hello")
user_service.notify_user("123", "Welcome!")

```

Dive into the **[full documentation](https://whiteducksoftware.github.io/wd-di/)** to explore service lifetimes, configuration, middleware, and more!

---

## Contributing 🤝

Contributions are welcome! Please see the main documentation site for details on how to contribute, report issues, or request features.

---

## License 📜

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.