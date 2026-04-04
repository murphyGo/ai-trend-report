"""재시도 유틸리티"""

import logging
import time
from functools import wraps
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Exponential backoff 재시도 데코레이터

    Args:
        max_retries: 최대 재시도 횟수 (기본: 3)
        base_delay: 기본 지연 시간 초 (기본: 1.0)
        max_delay: 최대 지연 시간 초 (기본: 30.0)
        exceptions: 재시도할 예외 타입들

    Returns:
        데코레이터 함수

    Example:
        @retry_with_backoff(max_retries=3, exceptions=(TimeoutError,))
        def fetch_data():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Exponential backoff: 1초, 2초, 4초, ...
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.info(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay:.1f}s due to: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.warning(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}"
                        )

            # 모든 재시도 실패 시 마지막 예외 발생
            raise last_exception

        return wrapper

    return decorator


def retry_with_backoff_return_none(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """재시도 후 실패 시 None 반환하는 데코레이터

    예외를 발생시키지 않고 None을 반환합니다.
    기존 코드와의 호환성을 위해 사용합니다.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.info(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay:.1f}s due to: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.warning(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}"
                        )
                        return None

            return None

        return wrapper

    return decorator
