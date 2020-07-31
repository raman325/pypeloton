import asyncio
from functools import wraps
from typing import Callable


def async_to_sync(f: Callable) -> Callable:
    """Decorator to run async function as sync."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper
