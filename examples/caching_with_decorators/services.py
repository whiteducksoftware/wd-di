# examples/caching_with_decorators/services.py
import time
from abc import ABC, abstractmethod

class IExternalWeatherService(ABC):
    @abstractmethod
    def get_current_temperature(self, city: str) -> float:
        """Simulates fetching current temperature for a city."""
        pass

class SlowExternalWeatherService(IExternalWeatherService):
    """A simulated weather service that is intentionally slow."""
    def __init__(self):
        self._call_count = 0

    def get_current_temperature(self, city: str) -> float:
        self._call_count += 1
        print(f"[SlowExternalWeatherService] Fetching temperature for {city}... (Call #{self._call_count})")
        time.sleep(2) # Simulate network latency or expensive computation
        if city.lower() == "london":
            temp = 15.0 + self._call_count # Make it change slightly to show cache effect
            print(f"[SlowExternalWeatherService] Temperature for London: {temp}°C")
            return temp
        elif city.lower() == "new york":
            temp = 22.0 + self._call_count
            print(f"[SlowExternalWeatherService] Temperature for New York: {temp}°C")
            return temp
        else:
            temp = 10.0 + self._call_count
            print(f"[SlowExternalWeatherService] Temperature for {city}: {temp}°C")
            return temp

    def get_api_call_count(self) -> int:
        return self._call_count 