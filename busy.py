import logging
import timeit
from flstr import FLCallable


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


# Minimum overhead to apply the string formatting

def busy_standard_logger_formatted(n):
    for i in range(n):
        log.debug("Log entry: %s" % (i,))


def busy_f_string_logger(n):
    for i in range(n):
        log.debug(f"Log entry: {i}")


# Use the FLCallable wrapper class. While still not fast enough - about 2x
# slower than just a plain tuple here - a builtin type should make equivalent to
# a regular tuple, plus avoid other desugaring overhead.

def busy_lambda_fl_string_logger(n):
    for i in range(n):
        log.debug(FLCallable(
            lambda self, cb: f"Log Entry: {cb(self, i, 0, '')}",
            "LogEntry: {i}"))


# Test with minimal overhead - we rely on here that log.debug doesn't actually
# evaluate its arg *given* the NullHandler (otherwise many `TypeError`s will

def busy_lambda_tuple_fl_string_logger(n):
    for i in range(n):
        log.debug((
            lambda self, cb: f"Log Entry: {cb(self, i, 0, '')}",
            "LogEntry: {i}"))


# FIXME print more detailed timing metrics
def time_code(name, stmt):
    print(name,
          timeit.timeit(
              stmt,
              globals=globals(),
              number=10000))


if __name__ == '__main__':
    time_code("%s logging", "busy_standard_logger(100)")
    time_code("%s logging, with formatting", "busy_standard_logger_formatted(100)")  
    time_code("f-string logging", "busy_f_string_logger(100)")
    time_code("Lambda fl-string logging", "busy_lambda_fl_string_logger(100)")
    time_code("Lambda fl-string logging (tuple only to simulate being builtin)",
                "busy_lambda_tuple_fl_string_logger(100)")

