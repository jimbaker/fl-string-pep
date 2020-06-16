# mypy: disallow-untyped-defs

from typing import Callable, Dict

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

dutch = {
    "{person} invites {num_guests} guests to their party":
    "{person} nodigt {num_guests} gasten uit op hun feest",
}
languages = {"nl": dutch}

def translate(fl: FL, lang: str) -> str:
    langdb = languages.get(lang, {})
    translated = langdb.get(fl.raw, fl.raw)
    table: Dict[str, object] = {}
    def callback(value: object, spec: str, text: str) -> str:
        table[text] = value
        return "{}"
    fl(callback)
    return translated.format(**table)

person = "Guido"
num_guests = 42
sentence = FL("{person} invites {num_guests} guests to their party",
              lambda cb:
              f"{cb(person, '', 'person')} "
              f"invites {cb(num_guests, '', 'num_guests')} "
              f"guests to their party")
print(translate(sentence, "en"))  # Guido invites 42 guests to their party
print(translate(sentence, "nl"))  # Guido nodigt 42 gasten uit op hun feest
