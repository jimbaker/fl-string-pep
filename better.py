# mypy: disallow-untyped-defs

"""L-strings and T-strings.

An L-string, written l"...", is similar in form to an F-string (f"...").
However, instead of evaluating and formatting the interpolated expressions and
combining them with the fixed text into a string object, it produces an object
that contains all information needed to produce that string object.  In this
object, the expressions to be interpolated are represented as lambdas which can
be called to evaluate them later.

A T-string, written t"...", is very similar to an L-string, but intended as a
marker for translatable objects.  T-strings also have a configurable mechanism
for producing a translation using a translation database (for example, using
the gettext module).  The configuration mechanism can use a global value or a
contextvar (PEP 567).

The segments of L-strings (and hence T-strings) are represented as Ellement
objects.  Each Ellement represents an interpolation followed by a fixed string
suffix.  The initial fixed string suffix is represented separately.

Special cases:

- If no colon is present, the format_spec is None.

- If the format_spec contains further interpolations, it is represented by an
  EllString.

Open issues:

- What to do with '=' and '!'?  Suggestion: keep them in the expr text and pass
  a format_mode flag argument which is 's', 'r', 'a' or None.  Then if '=' is
  given but neither '!' nor ':' is present, put 'r' in the fomat_mode argument.
  Alternatively, we could keep '=' in the expr text but not '!', and check for
  the presence of '=' using something like expr.rstrip().endswith('=').

  (Part of the issue here is that F-strings are being very clever here, and
  look separately for '=', '!' and ':', and construct a flag for the
  FORMAT_VALUE opcode.)

"""

from __future__ import annotations

from typing import *

__all__ = ["Ellement", "EllString", "TeeString"]


class Ellement:
    """Object to represent one segment of an L-string.

    The fields are supposed to be read-only and immutable.
    """

    __slots__ = ("expr", "call", "format_mode", "format_spec", "suffix")

    def __init__(self,
                 expr: str,  # Includes whitespace, '=', and !s/!r/!a if present
                 call: Callable[[], object],
                 format_mode: Optional[Literal['a', 'r', 's']],
                 format_spec: Optional[Union[str, EllString]],
                 suffix: str):
        self.expr = expr
        self.call = call
        self.format_mode = format_mode
        self.format_spec = format_spec
        self.suffix = suffix

    def raw(self) -> str:
        text = ["{", self.expr]
        if self.format_spec is not None:
            text.append(":")
            if isinstance(self.format_spec, EllString):
                text.append(self.format_spec.raw())
            else:
                text.append(self.format_spec)
        text.append("}")
        text.append(self.suffix)
        return "".join(text)

    _mode_map: Dict[Optional[str], Callable[[object], object]] = {
        'a': ascii, 's': str, 'r': repr, None: lambda x: x}

    def render(self) -> str:
        value = self.call()
        value = self._mode_map[self.format_mode](value)
        if self.format_spec is not None:
            value = format(value, str(self.format_spec))
        return f"{value}{self.suffix}"

    def __str__(self) -> str:
        return self.raw()

    def __repr__(self) -> str:
        items = tuple(map(repr, (self.format_mode, self.format_spec, self.suffix)))
        texts = (repr(self.expr), "<lambda>") + items
        return f"Ellement({', '.join(texts)})"


class EllString:
    """Object returned by L-string notation (l"...").

    The expression l"a{b}c{d:f}e" translates into the following
    constructor call:

        EllString("a",
                  Ellement("b", lambda: b, None, "c"),
                  Ellement("d", lambda: d, "f", "e"))

    The fields are supposed to be read-only and immutable.
    """

    __slots__ = ("prefix", "ellements")

    def __init__(self, prefix: str, *ellements: Ellement):
        self.prefix = prefix
        self.ellements = ellements

    def raw(self) -> str:
        text = [self.prefix]
        for ell in self.ellements:
            text.append(ell.raw())
        return "".join(text)

    def render(self) -> str:
        text = [self.prefix]
        for ell in self.ellements:
            text.append(ell.render())
        return "".join(text)

    def __repr__(self) -> str:
        return "l" + repr(self.raw())

    def __str__(self) -> str:
        return self.render()


# Set this to a Callable[[TeeString], str] to customize TeeString.render()
# (and hence TeeString.__str__()).  This could be something using
# gettext.gettext() or something that further delegates using a
# thread-local or a contextvar.
override_tee_string_render = None


class TeeString(EllString):
    """Object returned bt T-string notation (t"...").

    The constructor signature and attributes are the same as for
    EllString.
    """

    __slots__ = ()

    def render(self) -> str:
        if override_tee_string_render is not None:
            return override_tee_string_render(self)
        return super().render()
