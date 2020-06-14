from collections import namedtuple


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

i = 47
fl = FLCallable(
    lambda self, cb: f"Log Entry: {cb(self, i) if cb else i}",
    "LogEntry: {i}")
print(fl)

def doubler(obj, value):
    print(f"Working with {obj=}: {value=}")
    return value * 2

print(fl(doubler))

