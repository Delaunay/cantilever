import time


from reactivex import operators as ops


def fibonacci_of(nn):
    # slow implementation so we can measure something
    if nn in {0, 1}:
        return nn
    return fibonacci_of(nn - 1) + fibonacci_of(nn - 2)


def fake_work():
    fibonacci_of(28)


def metrics(source, observer, scheduler):
    def rate(pair):
        start = pair[0]
        end = pair[1]

        batch_size = start["batch_size"]
        start_time = start["time"]
        end_time = end["time"]
        elapsed = (end_time - start_time) * 1e-9

        return {"name": "perf", "rate": batch_size / elapsed, "elapsed": elapsed}

    def filter_obj(obj):
        # print(obj)
        return "name" in obj and obj["name"] == "batch"

    rate_stream = source.pipe(ops.filter(filter_obj), ops.pairwise(), ops.map(rate))

    rate_stream.subscribe(
        on_next=lambda value: print(value),
        on_error=lambda error: print("Error:", error),
    )

    avg = rate_stream.pipe(ops.average(lambda x: x["rate"]))

    avg.subscribe(
        on_next=lambda value: print(f"Average: {value}"),
        on_error=lambda error: print("Error:", error),
    )


n = 60
qsize = 200


def test_counters_shm():
    from cantilever.core.perfcounter_shm import PerfCounter, Source

    with PerfCounter(Source, (metrics,), qsize) as counter:
        for _ in range(n):
            counter.push_object(name="batch", time=time.time_ns(), batch_size=1024)
            fake_work()


def test_counters_queue():
    from cantilever.core.perfcounter_queue import PerfCounter, Source

    with PerfCounter(Source, (metrics,), qsize) as counter:
        for _ in range(n):
            counter.push_object(name="batch", time=time.time_ns(), batch_size=1024)
            fake_work()


def test_counters_thread():
    from cantilever.core.perfcounter_thread import PerfCounter, Source

    with PerfCounter(Source, (metrics,), qsize) as counter:
        for _ in range(n):
            counter.push_object(name="batch", time=time.time_ns(), batch_size=1024)
            fake_work()


def counters_nothing():
    s = time.time_ns()

    for _ in range(n):
        fake_work()

    e = time.time_ns()

    elapsed = (e - s) * 1e-9
    count = 1024 * n
    return count / elapsed, elapsed / n


if __name__ == "__main__":
    target, elapsed = counters_nothing()

    test_counters_thread()
    test_counters_shm()
    test_counters_queue()

    print(f"Target is {target} | {elapsed}")
