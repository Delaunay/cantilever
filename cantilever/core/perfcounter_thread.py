import time
import queue
import traceback
import threading
import queue

SHM_INDEX_IN = -1
SHM_INDEX_OUT = -2
SHM_ON = -3
SHM_SIZE = -4
SHM_MAX = 4


class Observer:
    def __init__(self) -> None:
        pass

    def __call__(self, key, value):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _worker(buffer: queue.Queue, observer_cls, observer_args, state):
    def event_loop():
        if state[SHM_ON] == 0:
            return False

        while True:
            try:
                msg = buffer.get_nowait()

                observer(msg)
            except queue.Empty:
                return True

            except Exception:
                traceback.print_exc()

        return True

    # worker turned on
    state[SHM_ON] = 1

    try:
        observer = observer_cls(*observer_args)

        with observer:
            while True:
                if not event_loop():
                    break

    except Exception:
        traceback.print_exc()

    finally:
        state[SHM_ON] = 0


class NotInitialized(Exception):
    pass


class Backpressure(Exception):
    pass


class WorkerStopped(Exception):
    pass


class PerfCounter:
    def __init__(self, observer_cls, observer_args, size=30):
        self.queue = queue.Queue(size)
        self.state = dict()             # <= this guy is relying on GIL
        self.worker = None
        self.size = size
        self.observer_cls = observer_cls
        self.observer_args = observer_args
        self.worker = None

    def __enter__(self):
        self._init_worker()
        return self

    def _init_worker(self):
        self.state[SHM_ON] = 0
        self.worker = threading.Thread(
            target=_worker,
            args=(self.queue, self.observer_cls, self.observer_args, self.state),
        )
        self.worker.start()
        self._wait_worker_init()

    def _wait_worker_init(self):
        while not self.state[SHM_ON]:
            time.sleep(0.1)

    def wait(self):
        while not self.queue.empty():
            time.sleep(0.1)

    def __exit__(self, *args):
        self.wait()
        self.state[SHM_ON] = 0
        self.worker.join()

    def push_object(self, **kwargs):
        if self.state[SHM_ON] == 0:
            raise WorkerStopped()

        self.queue.put_nowait(kwargs)


my_perf_counter = time.perf_counter_ns


class ObjectAssembler(Observer):
    def __init__(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return

    def push(self, object):
        pass

    def __call__(self, obj):
        self.push(obj)


class Source(ObjectAssembler):
    def __init__(self, handler) -> None:
        super().__init__()
        self.reactivex_observer = None
        self.reactivex_scheduler = None
        self.source = None
        self.handler = handler
        self.pending = []

    def __enter__(self):
        def make(observer, scheduler):
            self.reactivex_observer = observer
            self.reactivex_scheduler = scheduler

        import reactivex as rx

        self.source = rx.create(make)
        self.handler(
            self.source,
            lambda: self.reactivex_observer,
            lambda: self.reactivex_scheduler,
        )
        return self

    def __exit__(self, *args):
        if self.reactivex_observer:
            self.reactivex_observer.on_completed()
        else:
            raise RuntimeError("reactivex_observer was never set")
        return

    def push(self, object):
        if self.reactivex_observer:
            if self.pending:
                for obj in self.pending:
                    self.reactivex_observer.on_next(obj)

            self.reactivex_observer.on_next(object)
        else:
            self.pending.append(object)
