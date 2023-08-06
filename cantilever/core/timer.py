import sys
import time
from contextlib import contextmanager
from .statstream import StatStream


profile = dict()



class Value:
    def __init__(self) -> None:
        self.value = None

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class StatStreamValue:
    def __init__(self) -> None:
        self.value = StatStream(0)

    def set(self, value):
        self.value.update(value, weight=1)

    def get(self, value):
        return self.value.current_obs


class TimerGroup:
    def __init__(self, name, value_type=Value) -> None:
        self.start = None
        self.end = None
        self.name = name
        self.timing = value_type()
        self.subgroups = dict()

    def latest(self):
        if self.end:
            return self.timing.get()

        return time.time() - self.start

    def __enter__(self):
        global timer_builder

        self.start = time.time()
        timer_builder.append(self)
        return self

    def __exit__(self, *args):
        global timer_builder
        self.end = time.time()
        self.timing.set(self.end - self.start)

        if timer_builder:
            timer_builder.pop()

    def show(self, depth=1):
        col = 40 - depth
        idt = depth * " "
        l = max(col - len(self.name), 0)
        sep = {0: "_", 1: ".", 2: " "}[depth % 3]

        print(f"{idt}{self.name} {sep * l} {self.latest():5.2f}")
        if len(self.subgroups) > 0:
            for _, v in self.subgroups.items():
                v.show(depth + 1)

    def timeit(self, name):
        timer = TimerGroup(name)
        self.subgroups[name] = timer
        return timer


timer_builder = []
TimerGroup("root").__enter__(),


@contextmanager
def timeit(name):
    timer = timer_builder[-1]

    with timer.timeit(name) as timer:
        yield timer


def timeitdec(func):
    def _(*args, **kwargs):
        with timeit(func.__name__):
            return func(*args, **kwargs)
    
    return _



def show_timings():
    if "-xyz" not in sys.argv:
        return

    print()
    print("Timings:")
    timer = timer_builder[0]
    timer.__exit__()
    timer.show()



# 
from multiprocessing import Pool

result = Pool().apply_async()