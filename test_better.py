from better import *


def test_basic():
    spam = "<SPAM>"
    ham = "<HAM>"
    # ell = l"Spam {spam} Ham {ham:_<10s} Eggs"
    ell = EllString("Spam ",
                    Ellement("spam", lambda: spam, None, None, " Ham "),
                    Ellement("ham", lambda: ham, None, "_<10s", " Eggs"))
    assert ell.raw() == "Spam {spam} Ham {ham:_<10s} Eggs"
    assert ell.render() == "Spam <SPAM> Ham <HAM>_____ Eggs"


def test_ellement_with_ell_string():
    eggs = 42
    # The format spec is "{fill}{align}{width}d"
    fill = "_"
    align = "<"
    width = 5
    fill_ell = Ellement("fill", lambda: fill, None, None, "")
    align_ell = Ellement("align", lambda: align, None, None, "")
    width_ell = Ellement("width", lambda: width, None, None, "d")
    format_spec = EllString("", fill_ell, align_ell, width_ell)
    assert format_spec.render() == "_<5d"
    ellem = Ellement("eggs",
                     lambda: eggs,
                     None,
                     format_spec,
                     ".")
    assert ellem.render() == "42___."
    assert str(ellem) == "{eggs:{fill}{align}{width}d}."
    assert repr(ellem) == "Ellement('eggs', <lambda>, None, l'{fill}{align}{width}d', '.')"
