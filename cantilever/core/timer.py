import sys
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import get_native_id

from .statstream import StatStream

profile = dict()


def _append(timer):
    global timer_builder
    timer_builder[get_native_id()].append(timer)


def _pop():
    global timer_builder
    if timer_builder:
        timer_builder[get_native_id()].pop()


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

    def get(self):
        return self.value.current_obs


@dataclass
class DisplayConfig:
    decimal_format: str = "8.2"
    col_size: int = 40
    indent: str = " "
    sep: dict = field(default_factory=lambda: {0: "_", 1: ".", 2: " "})
    col_sep: str = "|"

    def line_separator(self, line_no):
        return self.sep[line_no % len(self.sep)]

    def decimal_size(self):
        return int(self.decimal_format.split(".")[0])


class TimerGroup:
    def __init__(self, name, value_type=StatStreamValue, show_on_end=False) -> None:
        self.start = None
        self.end = None
        self.name = name
        self.timing = value_type()
        self.type = value_type
        self.show_on_end = show_on_end
        self.subgroups = dict()

    def latest(self):
        if self.end:
            return self.timing.get()

        return time.time() - self.start

    def __enter__(self):
        self.start = time.time()
        self.end = None
        _append(self)
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.timing.set(self.end - self.start)
        _pop()

        if self.show_on_end:
            self.show()

    def _header(self, config: DisplayConfig):
        size = config.decimal_size()
        col_sep = config.col_sep

        if isinstance(self.timing, StatStreamValue):
            header = [
                col_sep,
                f"{'avg':>{size}}",
                col_sep,
                f"{'total':>{size}}",
                col_sep,
                f"{'sd':>{size}}",
                col_sep,
                f"{'count':>{size}}",
            ]
            print(f"# {' ' * 40} {' '.join(header)}")
        else:
            print(f"# {' ' * 40} | latest")

    def _stats(self, config: DisplayConfig):
        df = config.decimal_format
        col_sep = config.col_sep

        if isinstance(self.timing, StatStreamValue):
            stat: StatStream = self.timing.value
            stats = [
                col_sep,
                f"{stat.avg:{df}f}",
                col_sep,
                f"{stat.total:{df}f}",
                col_sep,
                f"{stat.sd:{df}f}",
                col_sep,
                f"{stat.count:{df}f}",
            ]
            return " ".join(stats)

        return f"{self.latest():5.2f}"

    def show(self, depth=1, config: DisplayConfig = DisplayConfig()):
        col = config.col_size - depth
        idt = depth * config.indent
        length = max(col - len(self.name), 0)
        sep = config.line_separator(depth)

        if depth == 1:
            self._header(config=config)

        print(f"#{idt}{self.name} {sep * length} {self._stats(config=config)}")

        if len(self.subgroups) > 0:
            for _, v in self.subgroups.items():
                v.show(depth + 1, config=config)

    def iterator(self, iterator):
        while True:
            with self.timeit("next"):
                try:
                    batch = next(iterator)
                except StopIteration:
                    return
            yield batch

    def timeit(self, name, show_on_end=False):
        timer = self.subgroups.get(name)

        if timer is None:
            timer = TimerGroup(name, value_type=self.type, show_on_end=show_on_end)
            self.subgroups[name] = timer

        return timer


timer_builder = defaultdict(list)
TimerGroup("root").__enter__()


def timeiterator(*args):
    return _current().iterator(*args)


def _current() -> TimerGroup:
    global timer_builder
    timerlist = timer_builder[get_native_id()]

    if len(timerlist) == 0:
        TimerGroup(f"root: {get_native_id()}").__enter__()

    return timerlist[-1]


def runtime():
    return _current().safe_total()


@contextmanager
def timeit(name, show_on_end=False):
    timer = _current()

    with timer.timeit(name, show_on_end=show_on_end) as timer:
        yield timer


def timeitdec(func):
    def _(*args, **kwargs):
        with timeit(func.__name__):
            return func(*args, **kwargs)

    return _


def show_timings(force=False, config: DisplayConfig = DisplayConfig()):
    if not force and "-xyz" not in sys.argv:
        return

    print()
    print("Timings:")

    for _, thread_group in timer_builder.items():
        timer = thread_group[0]
        try:
            timer.__exit__()
        except:
            pass

        timer.show(config=config)
        print("")
