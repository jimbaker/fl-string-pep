import logging
from collections import namedtuple


log = logging.getLogger("busy")
log.addHandler(logging.NullHandler())


# None of these examples actually write log records (given the NullHandler), so
# we are just measuring the cost to do some necessary setup in case we did do
# so. Given that fl-strings are deferred like %s style strings for logging, this
# hopefully shows opportunities for improvement - even in the simplest possible
# log message that requires composition.

def busy_standard_logger(n):
    for i in range(n):
        log.debug("Log entry: %s", i)


def busy_f_string_logger(n):
    for i in range(n):
        log.debug(f"Log entry: {i}")


# Starting wrapper class. While still not fast enough - about 2x slower than
# just a plain tuple here - a builtin type should make equivalent to a regular
# tuple, plus avoid other desugaring overhead. It will likely have a few more
# methods, not to mention a lowercase name to follow convention for such types.

FLCallableBase = namedtuple("FLCallable", ["call", "call_ex", "raw"])

class FLCallable(FLCallableBase):
    def __call__(self):
        return self.call(self)


def busy_lambda_fl_string_logger(n):
    for i in range(n):
        log.debug(FLCallable(
            lambda self: f"Log Entry: {i}",
            lambda self, cb: f"{cb(self, i)}",
            "LogEntry: {i}"))


# Test with minimal overhead

def busy_lambda_tuple_fl_string_logger(n):
    for i in range(n):
        log.debug((
            lambda self: f"Log Entry: {i}",
            lambda self, cb: f"{cb(self, i)}",
            "LogEntry: {i}"))


if __name__ == '__main__':
    import timeit
    print("%s logging",
        timeit.timeit(
            "busy_standard_logger(100)",
            globals=globals(),
            number=10000))

    print("f-string logging",
        timeit.timeit(
            "busy_f_string_logger(100)",
            globals=globals(),
            number=10000))

    print("Lambda fl-string logging",
        timeit.timeit(
            "busy_lambda_fl_string_logger(100)",
            globals=globals(),
            number=10000))

    print("Lambda fl-string logging (tuple only to simulate being builtin)",
        timeit.timeit(
            "busy_lambda_tuple_fl_string_logger(100)",
            globals=globals(),
            number=10000))

    
    x = timeit.timeit(
        "busy_lambda_fl_string_logger(100)",
        globals=globals(),
        number=10000)
