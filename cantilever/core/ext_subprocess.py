import multiprocessing
import os
import subprocess
import time


def popen_reader(state: dict, function, args, shell=False):
    """Execute a command with the given formatter."""
    with subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=shell,
    ) as process:
        try:
            while process.poll() is None:
                line = process.stdout.readline()

                if len(line) > 0:
                    function(line, state)

            return process.poll()
        except KeyboardInterrupt:
            print("Stopping due to user interrupt")
            process.kill()

        return -1



class MongoInstance:
    def __init__(self, cmd, args) -> None:
        self.env = {}
        self.manager = multiprocessing.Manager()
        self.state = self.manager.dict()
        self.state["error"] = 0
        self.proc = None
        self.cmd = cmd
        self.args = args

    def shutdown(self):
        if self.proc:
            self.proc.terminate()

    def __enter__(self):
        self.shutdown()

        for k, v in self.env.items():
            os.environ[k] = str(v)

        try:
            self.proc = multiprocessing.Process(
                target=popen_reader, 
                args=(self.state, function, [self.cmd, *self.args]),
            )
            self.proc.start()
            while self.proc.is_alive() and self.state.get("ready", 0) != 1:
                time.sleep(0.01)

        except:
            self.shutdown()
            raise
        return self

    def __exit__(self, *args):
        self.shutdown()
        self.proc.terminate()

        while self.proc.is_alive():
            time.sleep(0.01)

