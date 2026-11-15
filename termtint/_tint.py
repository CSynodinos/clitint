from typing import Any
import re
import os
import sys


#* The variables that decide whether text is coloured (see ``colours_on``), in the order they are asked.
COLOURS_OFF = "TERMTINT_COLOURS_OFF"
NO_COLOR = "NO_COLOR"
ANSI_COLORS_DISABLED = "ANSI_COLORS_DISABLED"
FORCE_COLOR = "FORCE_COLOR"
TERM = "TERM"

#* The attributes a spec may name, and the sequence that switches each on. Written in front of a colour.
ATTRIBUTES: dict[str, str] = {
    "bold": "\x1b[1m", "dim": "\x1b[2m", "italic": "\x1b[3m", "underline": "\x1b[4m",
    }
#* The colours, as the text's colour. ``on_<colour>`` is the same colour as its background.
#* The sequences are the ones termcolor writes (``orange`` is its (255, 165, 0)), so text made
#* with termcolor and with termtint is the same, byte for byte.
COLOURS: dict[str, str] = {
    "black": "\x1b[30m", "red": "\x1b[31m", "green": "\x1b[32m", "yellow": "\x1b[33m", "blue": "\x1b[34m",
    "magenta": "\x1b[35m", "cyan": "\x1b[36m", "white": "\x1b[37m", "grey": "\x1b[90m",
    "orange": "\x1b[38;2;255;165;0m",
    }
BACKGROUNDS: dict[str, str] = {
    "black": "\x1b[40m", "red": "\x1b[41m", "green": "\x1b[42m", "yellow": "\x1b[43m", "blue": "\x1b[44m",
    "magenta": "\x1b[45m", "cyan": "\x1b[46m", "white": "\x1b[47m", "grey": "\x1b[100m",
    "orange": "\x1b[48;2;255;165;0m",
    }
RESET = "\x1b[0m"


#* What ``turn_colours_off`` or ``turn_colours_on`` chose, or None: the environment and the streams decide.
_CHOSEN: bool | None = None


def turn_colours_off() -> None:
    """Plain text from now on, whatever the environment and the streams say (as ``TERMTINT_COLOURS_OFF=1``)."""
    global _CHOSEN
    _CHOSEN = False


def turn_colours_on() -> None:
    """Coloured text from now on, also where it goes to no terminal (as ``FORCE_COLOR``)."""
    global _CHOSEN
    _CHOSEN = True


def let_the_environment_decide() -> None:
    """Undo ``turn_colours_off`` / ``turn_colours_on``: the environment and the streams decide again."""
    global _CHOSEN
    _CHOSEN = None


def add_off_switch(name: str) -> None:
    """
    Make ``name=1`` switch colours off too, as ``TERMTINT_COLOURS_OFF=1`` does: for a library
    that offers its users a variable of its own (``add_off_switch("MYLIB_COLOURS_OFF")``). Only
    the value ``"1"`` counts. Asked with the other off switches, before ``FORCE_COLOR``.
    """
    global _OFF, _K_OFFS
    if not isinstance(name, str) or not name:
        raise TypeError(f"an off switch is the name of an environment variable, not {name!r}")
    if name in _OFF:
        return
    _OFF = (*_OFF, name)
    if _FAST:
        _K_OFFS = (*_K_OFFS, _encode_key(name))


def colours_on() -> bool:
    """
    Whether text is coloured now.

    A string doesn't know where it will end up: an uncaught error goes to stderr, ``print`` to
    stdout, a logger to a file. So colours are used only when both standard streams are
    terminals. Redirect either one (``2> errors.log``, ``| less``, a CI job) and text is plain:
    no escape sequence lands in a file.

    ``turn_colours_off`` and ``turn_colours_on`` decide before anything else. Then the
    environment, in this order: ``TERMTINT_COLOURS_OFF=1`` (and each ``add_off_switch``), ``NO_COLOR`` and
    ``ANSI_COLORS_DISABLED`` switch colours off, ``FORCE_COLOR`` switches them on whatever the
    streams are, and ``TERM=dumb`` switches them off. Read at every call, so a change takes
    effect at once.
    """
    if _CHOSEN is not None:                             # turn_colours_off / turn_colours_on: the program has said
        return _CHOSEN
    env = os.environ
    #* Read from ``os.environ`` as it is now: a program may have put another mapping in its place.
    data = getattr(env, "_data", None) if _FAST else None
    if type(data) is not dict:
        if NO_COLOR in env or ANSI_COLORS_DISABLED in env:
            return False
        for name in _OFF:
            if env.get(name) == "1":
                return False
        if FORCE_COLOR in env:
            return True
        if env.get(TERM) == "dumb":
            return False
        return _both_terminals()
    if _K_NO_COLOR in data or _K_ANSI in data:
        return False
    for key in _K_OFFS:
        if data.get(key) == _V_ONE:
            return False
    if _K_FORCE in data:
        return True
    if data.get(_K_TERM) == _V_DUMB:
        return False
    return _both_terminals()


#* ``os.environ`` encodes the name at every lookup and decodes the value: five of them took 1 µs.
#* Below it is the dictionary it keeps, which is asked directly, with the names and the two
#* values encoded once, the way ``os.environ`` does it on this platform. It is the same data:
#* what ``os.environ`` is given lands there. Where a Python has no such dictionary (it is a
#* CPython detail), ``os.environ`` is asked as usual.
#* The variables that switch colours off with the value "1": termtint's own, then each ``add_off_switch``.
_OFF: tuple[str, ...] = (COLOURS_OFF,)
_K_OFFS: tuple[Any, ...] = ()
_FAST = False
try:
    _encode_key, _encode_value = os.environ.encodekey, os.environ.encodevalue
    _K_OFFS = (_encode_key(COLOURS_OFF),)
    _K_NO_COLOR, _K_ANSI, _K_FORCE, _K_TERM = (
        _encode_key(name) for name in (NO_COLOR, ANSI_COLORS_DISABLED, FORCE_COLOR, TERM)
        )
    _V_ONE, _V_DUMB = _encode_value("1"), _encode_value("dumb")
    _FAST = type(os.environ._data) is dict                                          # type: ignore[attr-defined]
except Exception:
    _FAST = False


#* (sys.stdout, sys.stderr, whether both are terminals): asked again only when a stream was replaced.
_streams: tuple[Any, Any, bool] = (None, None, False)


def _both_terminals() -> bool:
    global _streams
    out, err = sys.stdout, sys.stderr
    if _streams[0] is out and _streams[1] is err:
        return _streams[2]
    answer = _is_terminal(out) and _is_terminal(err)
    _streams = (out, err, answer)
    return answer


def _is_terminal(stream: Any) -> bool:
    try:
        return bool(stream.isatty())
    except Exception:                   # no stream at all (pythonw), a closed one, an object without isatty
        return False


#* While one message is built: the answer of ``colours_on`` for all of it (None: ask each time).
_decided: bool | None = None


def decide() -> bool:
    """
    Ask ``colours_on`` once and keep the answer: every ``formatter`` and ``coloured`` call gives
    it until ``release()``. For a message built of many coloured words (the environment is slow
    to read). The functions are the fast form of ``one_decision``; mind to call ``release``.
    """
    global _decided
    _decided = answer = colours_on()
    return answer


def decision() -> bool | None:
    """The answer ``decide`` kept, or None where nothing has been decided."""
    return _decided


def release() -> None:
    """Forget the answer ``decide`` kept: each call asks ``colours_on`` again."""
    global _decided
    _decided = None


class one_decision:
    """
    ``with one_decision():`` around the building of one message asks once whether it is
    coloured, where every ``formatter`` call in it would ask again. Inside another one it keeps
    the outer answer, and leaves it in place. Not for threads that build messages at once: the
    decision is the module's.
    """
    __slots__ = ("_outer",)

    def __enter__(self) -> bool:
        global _decided
        self._outer = _decided
        if _decided is None:
            _decided = colours_on()
        return _decided

    def __exit__(self, *_: Any) -> None:
        global _decided
        _decided = self._outer
        return


def coloured() -> bool:
    """Whether the message being built is coloured: the one decision made for it, or ``colours_on()``."""
    return colours_on() if _decided is None else _decided


def _escapes(spec: str) -> tuple[str, str]:
    """
    What is written in front of and behind a text for ``spec``: the attributes' sequences, then
    the colour's, then the background's, and the sequence that switches everything off.
    """
    attributes: list[str] = []
    colour = background = ""
    names = spec.split("_")
    i = 0
    while i < len(names):
        name = names[i]
        if name == "on" and i + 1 < len(names) and names[i + 1] in BACKGROUNDS:
            if background:
                raise ValueError(f"two backgrounds in {spec!r}")
            background = BACKGROUNDS[names[i + 1]]
            i += 2
            continue
        if name in ATTRIBUTES:
            if ATTRIBUTES[name] not in attributes:
                attributes.append(ATTRIBUTES[name])
        elif name in COLOURS:
            if colour and colour != COLOURS[name]:
                raise ValueError(f"two colours in {spec!r}: name one, and 'on_<colour>' for a background")
            colour = COLOURS[name]
        else:
            raise ValueError(
                f"unknown style {name!r} in {spec!r}: a spec is made of {', '.join(ATTRIBUTES)}, "
                f"{', '.join(COLOURS)} and on_<colour>, joined by '_'"
                )
        i += 1
    order = list(ATTRIBUTES.values())
    attributes.sort(key = order.index)
    return "".join(attributes) + colour + background, RESET


#* spec -> what ``_escapes`` answered.
_ESCAPES: dict[str, tuple[str, str]] = {}


def formatter(text: Any, spec: str) -> str:
    """
    ``text`` in the styles ``spec`` names, or as it is when colours are off (see ``colours_on``).

    Args:
        text (Any): The text, or any object: its ``str`` is what is written.
        spec (str): Styles joined by ``_``, in any order: ``"bold_red"``, ``"cyan"``,
            ``"underline_white_on_blue"``. Attributes: ``bold``, ``dim``, ``italic``,
            ``underline``. Colours: ``black``, ``red``, ``green``, ``yellow``, ``blue``,
            ``magenta``, ``cyan``, ``white``, ``grey``, ``orange``; ``on_<colour>`` is a
            background. Anything else is a ``ValueError``.

    Returns:
        str: The text between the escape sequences of its styles, or the plain text.

    Example:
        >>> formatter("hello", "bold_red")
        '\\x1b[1m\\x1b[31mhello\\x1b[0m'
    """
    if not (colours_on() if _decided is None else _decided):
        return str(text)
    escapes = _ESCAPES.get(spec)
    if escapes is None:
        escapes = _ESCAPES[spec] = _escapes(spec)
    return escapes[0] + str(text) + escapes[1]


def escapes(*specs: str) -> tuple[str, ...]:
    """
    What is written in front of and behind a text for each of ``specs``, in one flat tuple:
    ``before, after, before, after ...``. For a message put together in one f-string, with the
    sequences as constants: cheaper than a ``formatter`` call per coloured word. Always the
    sequences, whatever ``colours_on`` says: the caller decides (``coloured()``).
    """
    return tuple([part for spec in specs for part in _escapes(spec)])


_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip_colours(text: str) -> str:
    """``text`` without its colours: every ANSI style sequence taken out, the words left as they are."""
    return _ANSI.sub("", text)
