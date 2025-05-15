# Caching with Service Decorators Example

This example demonstrates how to use the service decorator functionality of the `wd-di` library to add a caching layer to a service.

## Scenario

We have an `IExternalWeatherService` that simulates fetching weather data from an external source. The concrete implementation, `SlowExternalWeatherService`, is intentionally slow to mimic network latency or computationally expensive operations. 

To improve performance and reduce calls to the slow service, we introduce a `CachingWeatherServiceDecorator`. This decorator wraps the `IExternalWeatherService` and caches its results for a configured duration.

## Files

*   `services.py`: Defines the `IExternalWeatherService` interface and the `SlowExternalWeatherService` implementation.
*   `decorators.py`: Defines the `CachingWeatherServiceDecorator` and `create_caching_weather_decorator_factory` which creates the actual decorator factory callable used for registration.
*   `main.py`: Sets up the `ServiceCollection`, registers the services, applies the caching decorator, and then demonstrates the caching behavior by calling the weather service multiple times for different cities and observing cache hits, misses, and expirations.

## How it Works

1.  **Service Registration**: In `main.py`, `SlowExternalWeatherService` is registered as a singleton for the `IExternalWeatherService` interface.
2.  **Decorator Factory Creation**: `create_caching_weather_decorator_factory(cache_duration_seconds=5)` is called. This function returns another function (the actual decorator factory) that is configured with a 5-second cache duration. This demonstrates how decorators can be parameterized.
3.  **Decorator Application**: `services.decorate(IExternalWeatherService, caching_factory)` tells the service collection that whenever `IExternalWeatherService` is resolved, it should be passed through the `caching_factory`.
4.  **Instance Creation & Decoration**: When `provider.get_service(IExternalWeatherService)` is first called:
    *   The `ServiceProvider` creates an instance of `SlowExternalWeatherService`.
    *   It then calls the `caching_factory`, passing the `ServiceProvider` and the `SlowExternalWeatherService` instance.
    *   The `caching_factory` returns an instance of `CachingWeatherServiceDecorator` which wraps the `SlowExternalWeatherService` instance.
    *   This decorated instance is returned to the caller.
5.  **Caching Logic**: 
    *   The `CachingWeatherServiceDecorator` maintains an in-memory cache (`self._cache`).
    *   When `get_current_temperature` is called, it first checks the cache for the given city.
    *   If a valid (non-expired) entry is found (Cache HIT), it returns the cached temperature.
    *   If the entry is missing or expired (Cache MISS/STALE), it calls the `get_current_temperature` method of the *inner* (`SlowExternalWeatherService`) instance, stores the result in the cache with a new timestamp, and then returns it.

## Running the Example

Navigate to the `examples/caching_with_decorators` directory and run:

```bash
python main.py
```

You will see output indicating cache hits, misses, and the calls made to the `SlowExternalWeatherService`. The simulated delays will make the effect of caching apparent.

This example showcases how decorators can add significant cross-cutting concerns like caching in a clean, modular, and maintainable way without modifying the original service implementation. 