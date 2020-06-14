from flstr import FLCallable


i = 47
# below is equivalent to c = fl"Log Entry: {i}"
c = FLCallable(
    lambda self, cb: f"Log Entry: {cb(self, i, 0, '')}",
    "LogEntry: {i}")
print(c)


# stand-in for some arbitrary i18n function
def doubler(obj, value, index, formatspec):
    print(f"Working with {obj=}: {value=}, {index=}, {formatspec=}")
    return value * 2

print(c(doubler))
