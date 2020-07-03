import dis
import types
import functools
from dataclasses import dataclass
from typing import Callable


@dataclass
class Quote:
    raw: str
    function: Callable

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    # NOTE https://en.wikipedia.org/wiki/Lambda_lifting seems to be the prior
    # art here. However, "lift" instead of "lambda lift" also somewhat different
    # meaning in functional programming. By analogy to functools.partial, which
    # has similar concerns if we were to survey FP, we will just call it "lift".
    #
    # Another name might be "uncurry"
    def lift(self, *varnames: str) -> "Quote":
        """Lambda lifts varnames to the embedded lambda function, return a new Quote

        Any varname that is not used in the freevar is ignored, as it would be
        in any usual code.

        Because of the compilation, this is a relatively expensive operation in
        pure Python, so it should be cached (outside of this specific object of
        course). However, it should be possible to optimize this in a specific
        scenario, at least for CPython and Jython.
        """
        
        def param_list(names):
            return ", ".join(names)
        
        code = self.function.__code__

        # FIXME do more generic patching - it should be possible to do the
        # following for some function `f`:
        #
        # 1. extract co_freevars from f.__code__
        # 2. make a simple lambda that references these freevars
        # 3. use like below
        # 4. then patch back in the original code object
        #
        # Such a function could then be `functools.lift`, and then just used
        # here for the specific implementation in Quote.

        wrapped = f"""
def outer({param_list(code.co_freevars)}):
    def lifted({param_list(varnames)}):
        return (lambda: {self.raw})()
"""
        capture = {}
        exec(wrapped, self.function.__globals__, capture)
        outer = capture["outer"]

        # Essential for tracing out what is going :)
        # import dis; dis.dis(outer)

        lifted_code = outer.__code__.co_consts[1]

        lifted = types.FunctionType(lifted_code, self.function.__globals__)

        functools.update_wrapper(lifted, self.function)

        return Quote(self.raw, lifted)


def test_scope():
    x = 47
    q = Quote("x+1", lambda: x + 1)
    print(f"{q()=}")
    q_x = q.lift("x")  # lift x out of the free var
    print(f"{q_x(42)=}") 
    q_x2 = q_x.lift("x")  # ignore extra x in lifting again
    print(f"{q_x2(42)=}")
    try:
        # but we cannot lift the same variable twice in one lift, likely we want
        # some wrapper exception here
        q_xx = q_x.lift("x", "x")
    except SyntaxError as err:
        print(err)  # SyntaxError: duplicate argument 'x' in function definition
    q_xy = q_x.lift("x", "y")  # y is not used in the body, but that can be true of any function
    print(f"{q_xy(42, 99999)=}")


test_scope()
