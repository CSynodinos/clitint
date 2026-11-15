"""clitint: coloured terminal text with no dependencies, plain wherever it isn't read on a terminal."""
from ._tint import (
    formatter,
    strip_colours,
    colours_on,
    turn_colours_off,
    turn_colours_on,
    let_the_environment_decide,
    coloured,
    decide,
    decision,
    release,
    add_off_switch,
    escapes,
    one_decision,
    ATTRIBUTES,
    COLOURS,
    BACKGROUNDS,
    RESET,
    )

__version__ = "0.1.0"

__all__ = [
    "formatter",
    "strip_colours",
    "colours_on",
    "turn_colours_off",
    "turn_colours_on",
    "let_the_environment_decide",
    "one_decision",
    "coloured",
    "decide",
    "decision",
    "release",
    "add_off_switch",
    "escapes",
    "ATTRIBUTES",
    "COLOURS",
    "BACKGROUNDS",
    "RESET",
    ]
