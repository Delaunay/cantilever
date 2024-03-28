import multiprocessing
from multiprocessing.shared_memory import ShareableList
from multiprocessing.managers import SharedMemoryManager
import time
import json

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


def _worker(buffer: ShareableList, observer_cls, observer_args, in_lock, out_lock, on_lock, index=0):
    size = buffer[SHM_SIZE]  # len(buffer) == 84 but size == 20

    with on_lock:
        buffer[SHM_ON] = 1

    with observer_cls(*observer_args) as obserer:
        while buffer[SHM_ON] > 0:

            # Get the in lock to make sure we a reading a full value
            with in_lock:
                index_in = buffer[SHM_INDEX_IN]

            while buffer[SHM_INDEX_OUT] < index_in:
                # read only, no need for lock
                counter = buffer[SHM_INDEX_OUT]

                
                idx = (counter % size) * 2
                key = buffer[idx]
                value = buffer[idx + 1]

                obserer(key, value)

                # finished reading
                # make sure we do an atomic write
                with out_lock:
                    buffer[SHM_INDEX_OUT] = counter + 1


def _preallocate_buffer(size, key_size=256):
    template = []
    for i in range(size * 2):
        template.append(" " * 256)  # Key
        template.append(int(0))  # Value

    template.append(size)  # SHM_SIZE    -4
    template.append(0)  # SHM_ON         -3
    template.append(0)  # SHM_INDEX_OUT  -2
    template.append(0)  # SHM_INDEX_IN   -1

    return template


class NotInitialized(Exception):
    pass


class Backpressure(Exception):
    pass


class PerfCounter:
    def __init__(self, observer_cls, observer_args, size=20000, key_size=64):
        self.smm = SharedMemoryManager()
        self.ringbuffer = []
        self.worker = None
        self.key_size = key_size
        self.size = size
        self.observer_cls = observer_cls
        self.observer_args = observer_args
        self.out_lock = None
        self.in_lock = None
        self.worker = None

    def __enter__(self):
        self.smm.start()
        self.ringbuffer = self.smm.ShareableList(
            _preallocate_buffer(self.size, self.key_size)
        )
        self.out_lock = multiprocessing.Lock()
        self.in_lock = multiprocessing.Lock()
        self._init_worker()
        return self

    def _init_worker(self):
        on_lock = multiprocessing.Lock()
        self.worker = multiprocessing.Process(
            target=_worker,
            args=(self.ringbuffer, self.observer_cls, self.observer_args, self.in_lock, self.out_lock, on_lock),
        )
        self.worker.start()
        self._wait_worker_init(on_lock)

    def _wait_worker_init(self, on_lock):
        while True:
            with on_lock:
                is_ready = self.ringbuffer[SHM_ON]

            if is_ready:
                break

    def wait(self):
        # Wait for worker to catch up
        with self.in_lock:
            in_pos = self.ringbuffer[SHM_INDEX_IN]
    
        while True:
            with self.out_lock:
                out_pos = self.ringbuffer[SHM_INDEX_OUT]
            
            if out_pos == in_pos:
                break

    def __exit__(self, *args):
        self.wait()
        self.ringbuffer[SHM_ON] = 0
        self.worker.join()
        return self.smm.__exit__(*args)

    def push_object(self, **kwargs):
        in_index = self.ringbuffer[SHM_INDEX_IN]
        
        with self.out_lock:
            out_index = self.ringbuffer[SHM_INDEX_OUT]
        
        queued_items = in_index - out_index
        free_space = self.size - queued_items

        if free_space < (len(kwargs) + 2):
            raise Backpressure("Not enough slots to push object")

        idx = (in_index % self.size) * 2
        self.ringbuffer[idx] = "#s"
        in_index += 1

        for k, v in kwargs.items():
            idx = (in_index % self.size) * 2
            self.ringbuffer[idx] = k
            self.ringbuffer[idx + 1] = v
            in_index += 1

        idx = (in_index % self.size) * 2
        self.ringbuffer[idx] = "#e"
        in_index += 1

        # worker might be reading while we write
        with self.in_lock:
            self.ringbuffer[SHM_INDEX_IN] = in_index

    def _push_unsafe(self, key, value, counter):
        # no need to lock, we are the only one writing to it
        idx = (counter % self.size) * 2
        self.ringbuffer[idx] = key
        self.ringbuffer[idx + 1] = value

        # finished writing
        # "SHM_INDEX_IN" is read by the worker
        # and need to be locked to avoid partial reads
        with self.in_lock:
            self.ringbuffer[SHM_INDEX_IN] = counter + 1

    def push_unsafe(self, key, value):
        self._push_unsafe(key, value, self.ringbuffer[SHM_INDEX_IN])

    def push(self, key, value):
        if self.ringbuffer is None:
            raise NotInitialized("Shared memory is not initialized")

        in_index = self.ringbuffer[SHM_INDEX_IN]

        # worker could be writing to it
        # get the out lock to make sure writing is finished
        with self.out_lock:
            out_index = self.ringbuffer[SHM_INDEX_OUT]

        if (out_index + self.size + 1 <= in_index ):
            raise Backpressure("Worker is not able to process all those events")

        if len(key) > self.key_size:
            raise ValueError("Key is bigger than storage")

        self._push_unsafe(key, value, in_index)


my_perf_counter = time.perf_counter_ns




class ObjectAssembler(Observer):
    def __init__(self) -> None:
        self.fp = None
        self.acc = {}
        self.time_diff = 0
        self.count = 0
        self.start_time = None
        self.end_time = None
        self.object_building = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return 
    
    def push(self, object):
        pass

    def __call__(self, key, value):
        if key == "#s":
            self.acc = {}
            self.start_time = value
            self.object_building = True
            return

        if key == "#e":
            self.end_time = value
            self.time_diff = 0
            self.count = 0
            self.push(self.acc)
            self.acc = {}
            self.object_building = False
            return
        
        if self.object_building:
            self.acc[key] = value
        else:
            self.push({key: value})


class Source(ObjectAssembler):
    def __init__(self, handler) -> None:
        super().__init__()
        self.reactivex_observer = None
        self.reactivex_scheduler = None
        self.source = None
        self.handler = handler
        
    def __enter__(self):
        def make(observer, scheduler):
            print("WTF")
            self.reactivex_observer = observer
            self.reactivex_scheduler = scheduler
            print("HERE", observer, scheduler)

        import reactivex as rx
        self.source = rx.create(make)
        self.handler(self.source, self.reactivex_observer, self.reactivex_scheduler)
        return self

    def __exit__(self, *args):
        self.reactivex_observer.on_completed()
        return 
    
    def push(self, object):
        self.reactivex_observer.on_next(object)