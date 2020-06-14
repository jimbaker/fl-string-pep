Adding fl-string support for deferred evaluation of f-strings
=============================================================

Intro
-----

fl-strings support a **structured** way to defer evaluations of
f-strings by making them callable objects. Writing

.. code:: python

    i = 42
    log.debug(fl"Log entry: {i}")

desugars to something like the following equivalent Python code:

.. code:: python

    i = 42
    log.debug(FLCallable(
        lambda self, cb: f"Log Entry: {cb(self, i, 0, '')}",
        "LogEntry: {i}"))

Note that standard scope analysis of any referenced names applies,
including the support of nested scopes and observation of mutability. No
frame introspection needed.

``FLCallable`` can be implemented in Python, but it should be a builtin
type, similar to ``slice`` or ``range`` for performance:

.. code:: python

    FLCallableBase = namedtuple("FLCallable", ["call_ex", "raw"])

    class FLCallable(FLCallableBase):
        def identity(self, value, index, formatspec):
            return value.__format__(formatspec)

        def __call__(self, cb=identity):
            return self.call_ex(self, cb)

        __str__ = __call__

This approach supports the following:

-  Users can simply change their f-strings to fl-strings.

-  Existing libraries that only expect strings, including f-strings,
   work as expected, however, the stringification is deferred until used. (Note
   that if the expressions are based on mutating values, this may result in a
   different stringification each time - there are no one-shot semantics.
   Although one can always wrap a fl-string with such a function.)

-  Maintains f-string semantics, including observability of mutated
   variables in expressions and no use of frame introspection.

-  Support for such use cases as logging; internationalization (i18n);
   sanitizing expressions - especially user-sourced to prevent injection attacks
   - for such uses as HTML, shell, and SQL; and screening of PII data.

-  As with f-strings, it is possible to use ``r`` in the prefix to
   indicate the string is raw with respect to any escape character handling.

Previous work
-------------

This work builds on `PEP
501 <https://www.python.org/dev/peps/pep-0501/>`__ "General purpose
string interpolation" and `BPO
#32954 <https://bugs.python.org/issue32954>`__ "Lazy Literal String
Interpolation", and is further inspired by `JavaScript tagged template
literals <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals>`__.

API
---

fl-string objects have the following minimal API (document with type hints).
This can be considered to be equivalent to the following singleton class
implemented at the location of the fl-string. So this could be done with a
``type`` 3-arg constructor, or a custom C-based type, but for notational
convenience we will show it as follows:

.. code:: python

    class FL:
        def __call__(self) -> str:
            """Returns the wrapped f-string."""
            ...

        def call_ex(self, cb) -> Any:
            """Calls a callback `cb` per expression in the f-string. Although each callback should return a string, it's possible for the callback to record these calls, then for call_ex to return `Any` type.
            """
            ...

        @property
        def raw(self) -> str:
            """Returns the raw, unparsed string."""
            ...

        __str__ = __call__

Implementation
--------------

-  f-strings are simple, elegant, and performant, because they follow
   standardPython practice. We should do more of that.

-  fl-strings - where "l" might stand for "lazy" or "lambda" or that it should
   be used for logging, although I have nothing really invested here in terms of
   the prefix - "i" could work as in PEP 501, but I do think the ergomomics are
   easier - like f-strings, but lazy. Note that it's possible to also add in "r"
   to the prefix, much like f-strings.

With that, let's add the following observations:

Deferring the execution requires the standard Python approach by wrapping it in
a function. But nested scopes still apply in this case, as observed
in https://bugs.python.org/issue32954 This allows us to avoid approaches
like https://gitlab.com/warsaw/flufl.i18n/-/blob/master/flufl/i18n/\_translator.py#L64
which uses ``sys._getframe`` to access variables, or then having to do further
``eval`` - we just use what has been built with f-string.

Rewriting expressions for such purposes as sanitization requires a callback on
each expression. There are still some fiddly details to be worked out with
respect to this callback, with respect to what parameters it should take,
including the formatspec. A good example of a rewrite would be adding log record
attributes as we see
in https://www.python.org/dev/peps/pep-0501/#possible-integration-with-the-logging-module.
If log record attributes are in a namespace, say a new enum
``LogAttribute.NAME`` defined in logging, it's a straightforward and correct
rewriting to map to the current logger name. In contrast, in PEP 501, we have to
parse expressions like ``{'record.name'}`` and assume that it means that. I
think it's preferable to use namespaces to help manage this mapping.

Certain rewriting requires access to the original raw string. An example of this
would be using the raw string to look up the corresponding CLDR plural rules in
ICU (http://cldr.unicode.org/index/cldr-spec/plural-rules), with a specific
example here: http://userguide.icu-project.org/formatparse/messages Note that
there is *not* a 1-to-1 mapping between such f-strings and CLDR templates in
their syntax, but arguably it is sufficiently close that a simple mapping could
be done. So consider this example:

.. code:: python

    print(_(fl("{host} invites {guest} and {num_guests} other people to their party.}")))

where ``_`` is some arbitrary function that takes into account async context
vars or thread locals, etc, and also serves as a marker for static analyzing
this code for i18n. (Note: I'm not an i18n expert at all, but that's the purpose
of this PEP proces!)

Lastly, each of the two variants of the original fl-string source code is
needed:

-  The callback variant cannot be derived from the raw string at runtime
   without using ``sys._getframe``, because of the scope analysis. Such frame
   inspection at user level significantly impact performance as I understand it
   on IronPython and PyPy, and would have similar considerations for a possibly
   optimized Jython.

-  The raw variant cannot be reconstructed at runtime from one of the
   other variants without inspecting bytecode, and that's even worse than frame
   inspection (at least for implementations like Jython where such bytecode
   inspection requires it to be retrieved from a file).
