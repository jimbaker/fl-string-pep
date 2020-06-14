from collections import namedtuple


FLCallableBase = namedtuple("FLCallable", ["call", "call_ex", "raw"])


class FLCallable(FLCallableBase):
    def __call__(self):
        return self.call(self)

    __str__ = __call__


def get_log_entries(n):
    for i in range(n):
        yield FLCallable(
            lambda self: f"Log Entry: {i}",
            lambda self, cb: f"{cb(self, i)}",
            "LogEntry: {i}")()


if __name__ == "__main__":
    log_entries = list(get_log_entries(10))
    for entry in log_entries:
        print(entry)
