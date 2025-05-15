# API Reference

This section provides detailed documentation for the public API of the WD-DI library.

## Core Components

- [ServiceCollection](./service_collection.md): For registering services.
- [ServiceProvider & Scope](./service_provider.md): For resolving services and managing scopes.
- [ServiceLifetime](./lifetimes.md): Defines service lifetime options.
- [create_service_collection()](./create_service_collection.md): Helper to create a `ServiceCollection`.

## Middleware

- [Middleware Components](./middleware.md): Describes `IMiddleware`, `MiddlewarePipeline`, and built-in middleware.
- [Middleware DI Integration](./middleware_di.md): Covers `ApplicationBuilder` and `MiddlewareBuilder` for setting up middleware pipelines with DI.

## Configuration

- [Configuration System](./config.md): Details `IConfiguration`, `ConfigurationBuilder`, and `Options`. 