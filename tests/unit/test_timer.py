import time

from cantilever.core.timer import show_timings, timeit


def test_timer():

    with timeit("here"):
        for _ in range(10):
            with timeit("this"):
                time.sleep(0.1)

    show_timings(force=True)
