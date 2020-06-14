import logging
from collections import namedtuple


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("equiv")

# Use namedtuple objects, because they are lightweight and somewhat
# representative of a built-in type's performance

FLCallableBase = namedtuple("FLCallable", ["call_ex", "raw"])


class FLCallable(FLCallableBase):
    # Instrument FLCallable to show its behavior with respect to evaluation
    counter = [0]

    def __call__(self, cb=None):
        self.counter[0] += 1
        return self.call_ex(self, cb)

    __str__ = __call__


# Desired code in the loop
# log.debug(fl"Log Entry: {i}")

# Desugared with lambdas and corresponding code objects, which allows for
# placement of the fl-string anywhere an expression is allowed.

def log_stuff(n):
    for i in range(n):
        log.debug(FLCallable(
            lambda self, cb: f"Log Entry: {cb(self, i) if cb else i}",
            "LogEntry: {i}"))


def log_more_or_less():
    for level in [logging.INFO, logging.DEBUG]:
        log.setLevel(level)
        log_stuff(10)
        print(f"Log entries evaluated: {FLCallable.counter[0]}")


if __name__ == "__main__":
    log_more_or_less()



