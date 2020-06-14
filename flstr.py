from collections import namedtuple


FLCallableBase = namedtuple("FLCallable", ["call_ex", "raw"])


class FLCallable(FLCallableBase):
    def identity(self, value, index, formatspec):
        return value.__format__(formatspec)

    def __call__(self, cb=identity):
        return self.call_ex(self, cb)

    __str__ = __call__
