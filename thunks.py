import logging
import shlex
from string import Formatter


# FIXME look more at the engineering design of mutable callsites (and supporting
# machinery) in Java for inspiration on how to have set/reset behavior
# https://docs.oracle.com/javase/8/docs/api/java/lang/invoke/MutableCallSite.html
# https://docs.oracle.com/javase/8/docs/api/java/lang/invoke/SwitchPoint.html
# But this should be adequate for now.

# FIXME add more type hints - this is important to document this idea!

class Thunk:
    def __init__(self, tag, raw, function):
        self.tag = tag
        self.raw = raw
        self.function = function  # must always be specified with a default function to get symtab
        self.is_set = False

    def reset_target(self):
        self.is_set = False

    def set_target(self, rewriter):
        # NOTE right now this will race with respect to multiple threads
        # entering this method. Given sequential consistency semantics - every
        # entering thread will see self.is_set without reordering - so long as
        # tag.rewrite is idempotent, this is a reasonable behavior. There are
        # similar semantics in Java,
        # https://docs.oracle.com/javase/8/docs/api/java/lang/ClassValue.html,

        if self.is_set:
            return

        function_body = rewriter(self)

        # FIXME this scope analysis based on the freevar symtab is no doubt incomplete!
        cellvars = ", ".join(freevar for freevar in self.function.__code__.co_freevars)
        tag_name = self.tag.__class__.__name__ 
        wrapped = f"""
def outer({cellvars}):
    def inner_{tag_name}():
        return {function_body}
"""
        # Use to capture the side effect of defining `outer`
        capture = {}

        # Use the globals from the old function as well - note this is the inner
        # function, not the original outer function. Close enough.
        exec(wrapped, self.function.__globals__, capture)

        # FIXME Hard-coded index based on above, but should suffice for our demo
        # purposes - can always look for the inner function name, etc
        self.function.__code__ = capture["outer"].__code__.co_consts[1]

        # No more idempotent racing at this point - this avoids having to use a
        # lock on this method, which makes it harder to integrate with a
        # Python-based rewrite scheme that might do arbitrary things.
        self.is_set = True

    def __call__(self):
        return self.function()

    def __str__(self):
        return self.function()


# The following function could go into a `thunktools` helper library.
# Regardless, the name needs to be much more carefully considered!

# FIXME it would be nicer if we can avoid using a string-based callback, but
# instead reference in some fashion. Requires more thinking on the scope
# analysis!

def add_expr_callback(s, cb):
    def unparse(arg, separator):
        return f"{separator}{arg}" if arg else ""

    parts = []
    for text, expr, formatspec, conversion in Formatter().parse(s):
        parts.append(
            f"{text}{{{cb}({expr}{unparse(conversion, '!')}{unparse(formatspec, ':')})}}")
    return f'''f"{''.join(parts)}"'''


# Goes into a utility library - let's say `shell_literal_support`. Pretend it is
# in there for now.

class shell_literal:

    # NOTE Since the thunk is retuned by this call, the receiver in the callsite can
    # choose to do additional manipulations on it. We will need a demo of this
    # functionality.

    def __call__(self, thunk: Thunk) -> Thunk:
        # NOTE so it can be any rewrite function, here in this tag as a bound
        # method
        thunk.set_target(self.rewrite)
        return thunk

    def rewrite(self, thunk: Thunk) -> str:
        return add_expr_callback(thunk.raw, "shlex.quote")


shell_literal = shell_literal()


# Our pretend main module

sh = shell_literal  # simulate `from shell_literal_support import shell_literal as sh`

def print_dir(path):
    print(sh(Thunk(sh, r"ls -l {path}", lambda: f"ls -l {path}")))


print_dir(path="/Users/Jim Baker - Admin/App Code & More/*.py")


# Alternative, showing the use of the original default

class log_literal:
    def __call__(self, thunk: Thunk) -> Thunk:
        return thunk

l = log_literal()

logging.basicConfig(level=logging.DEBUG)
i = 47
logging.debug(l(Thunk(l, r"Log entry: {i:03d}", lambda: f"Log entry: {i:03d}")))
