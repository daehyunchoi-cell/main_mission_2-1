# budget_app/decorators.py
import time
import logging
import functools
from typing import Callable, TypeVar, Any

logging.basicConfig(
    filename="budget_app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

F = TypeVar("F", bound=Callable[..., Any])


def handle_errors(func: F) -> F:
    """예외를 잡아 사용자 메시지 출력 + 로그 기록"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            print(f"[오류] 파일을 찾을 수 없습니다: {e}")
            logging.error(f"{func.__name__} - FileNotFoundError: {e}")
        except ValueError as e:
            print(f"[오류] 잘못된 값입니다: {e}")
            logging.error(f"{func.__name__} - ValueError: {e}")
        except Exception as e:
            print(f"[오류] 예상치 못한 오류가 발생했습니다: {e}")
            logging.error(f"{func.__name__} - Exception: {e}")
    return wrapper  # type: ignore


def log_action(func: F) -> F:
    """함수 호출 시작/종료를 로그에 기록"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"START {func.__name__}")
        result = func(*args, **kwargs)
        logging.info(f"END   {func.__name__}")
        return result
    return wrapper  # type: ignore


def measure_time(func: F) -> F:
    """실행 시간 측정 후 콘솔 출력"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[{func.__name__}] 실행 시간: {elapsed:.4f}s")
        return result
    return wrapper  # type: ignore