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