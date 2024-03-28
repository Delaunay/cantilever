
import time


from cantilever.core.perfcounter import PerfCounter, Source


def metrics(source, observer, scheduler):
    def rate(pair):
        start = pair[0]
        end = pair[1]

        batch_size = start["batch_size"]
        start_time = start["time"]
        end_time = end["time"]
        observer.on_next({"rate": batch_size / (end_time - start_time)})


    print(source, observer, scheduler)
    rate_stream = (
        source
        .filter(lambda obj: obj["name"] == "batch")
        .pairwise()
        .map(rate)
    )



def test_counters():
    with PerfCounter(Source, (metrics,)) as counter:

        for _ in range(3000):
            counter.push_object(name="batch", time=time.time_ns(), batch_size=1024)
            time.sleep(0.1)


if __name__ == "__main__":
    test_counters()
