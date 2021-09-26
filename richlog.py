from rich.console import Console
from typing import Callable
from time import perf_counter
from functools import wraps

c = Console()


def dbg(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = perf_counter()
        c.rule()
        c.log(f'Starting {func.__name__}...')
        try:
            func(*args, **kwargs)
            stop_time = perf_counter()
            c.log(
                f'{func.__name__} finished in {stop_time - start_time:0.2f}'
            )
        except BaseException:
            c.log(
                f'{func.__name__} failed in {stop_time - start_time:0.2f}',
                log_locals=True
            )
        c.rule()
    return wrapper


@dbg
def test(t='foo', i='bar'):
    c.log(f'{t} plus {i} equals spam')


if __name__ == '__main__':
    test(t='Chimi', i='changa')

