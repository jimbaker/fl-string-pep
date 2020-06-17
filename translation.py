# mypy: disallow-untyped-defs

from __future__ import annotations

from contextvars import ContextVar
from typing import Callable, Dict, List, Optional

# Called for each interpolation.
#
# Args:
# - the value to be interpolated (not necessarily a string)
# - the format spec (default "")
# - the text of the interpolation (less the format spec)
#
# Returns:
# - the formatted value
#
# The default callback returns format(value, spec),
# ignoring the text.
#
CallbackType = Callable[[object, str, str], str]


def default_callback(value: object, format_spec: str, expr: str) -> str:
    return format(value, format_spec)


class FL:
    __slots__ = ["__raw", "__call"]

    def __init__(self, raw: str, call: Callable[[CallbackType], str]):
        self.__raw = raw
        self.__call = call

    @property
    def raw(self) -> str:
        return self.__raw

    def __call__(self, callback: CallbackType = default_callback) -> str:
        return self.__call(callback)

    def __str__(self) -> str:
        return self()

    def __repr__(self) -> str:
        return "fl" + repr(self.raw)


# Example with format_spec

width = 3.14
height = 42
label = "narrow box"

# Emulate s = fl"W={width:.3f}, H={height:.3f}, area={width*height:.2f}  # {label}"
s = FL("W={width:.3f}, H={height:.3f}, area={width*height:.2f}  # {label}",
       lambda cb:
       f"W={cb(width, '.3f', 'width')}, "
       f"H={cb(height, '.3f', 'height')}, "
       f"area={cb(width*height, '.2f', 'width*height')}  "
       f"# {cb(label, '', 'label')}")

print(s)
print(s(lambda val, spec, text: repr(val)))
print(repr(s))


# Translation example


class TS(FL):
    __slots__: List[str] = []

    def __call__(self, callback: CallbackType = None) -> str:
        tf = translator_cv.get()
        if tf is None:
            if callback is None:
                callback = default_callback
            return super().__call__(callback)
        return tf(self, callback)

    def __repr__(self) -> str:
        return "t" + repr(self.raw)


TranslatorFunctionType = Callable[[TS, Optional[CallbackType]], str]

# Per-context translator function
translator_cv: ContextVar[Optional[TranslatorFunctionType]] = \
  ContextVar("translation.callback", default=None)


dutch = {
    "{person} invites {num_guests} guests to their party":
    "{person} nodigt {num_guests} gasten uit op hun feest",
}
languages = {"nl": dutch}

# Per-context 2-letter lowercase language code
lang_cv: ContextVar[str] = ContextVar("translation.language", default="en")


def translate(fl: FL, lang: str=None) -> str:
    if lang is None:
        lang = lang_cv.get()
    langdb = languages.get(lang, {})
    translated = langdb.get(fl.raw, fl.raw)
    table: Dict[str, object] = {}
    def callback(value: object, spec: str, text: str) -> str:
        table[text] = value
        return "{}"
    FL.__call__(fl, callback)
    return translated.format(**table)


person = "Guido"
sentence = TS("{person} invites {num_guests} guests to their party",
              lambda cb:
              f"{cb(person, '', 'person')} "
              f"invites {cb(num_guests, '', 'num_guests')} "
              f"guests to their party")
print(repr(sentence))
num_guests = 42
print(translate(sentence, "en"))
print(translate(sentence, "nl"))
print(translate(sentence, "fr"))


def example_tf(ts: TS, callback: Optional[CallbackType]) -> str:
    if callback is not None:
        raise ValueError(f"Cannot pass callback to example_tf(): {callback}")
    return translate(ts)


translator_cv.set(example_tf)
num_guests = 41
print(sentence)
num_guests = 40
lang_cv.set("nl")
print(sentence)
