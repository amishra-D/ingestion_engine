
import logging
from functools import wraps
from time import perf_counter
from typing import Any, Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


def measure_time(
    func: Callable[P, R],
) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = perf_counter()

        try:
            return func(*args, **kwargs)
        finally:
            elapsed = perf_counter() - start
            logger.info(
                "PERF | function=%s | elapsed=%.3f ms",
                func.__qualname__,
                elapsed * 1000,
            )

    return wrapper