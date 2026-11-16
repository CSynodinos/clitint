from __future__ import annotations
import os
import sys

#* Neither ``typing`` nor ``re`` is imported at run time: ``typing`` (``re`` with it) was 3.4 ms of a
#* 4.1 ms start, for one ``Any``. Annotations are text (the future import); ``re`` is imported by
#* ``strip_colours``, the one function that needs it, at its first call.
TYPE_CHECKING = False
if TYPE_CHECKING:
    import re
    from typing import Any


#* The variables that decide whether text is coloured (see ``colours_on``), in the order they are asked.
COLOURS_OFF = "CLITINT_COLOURS_OFF"
NO_COLOR = "NO_COLOR"
ANSI_COLORS_DISABLED = "ANSI_COLORS_DISABLED"
FORCE_COLOR = "FORCE_COLOR"
TERM = "TERM"

#* The attributes a spec may name, and the sequence that switches each on. Written in front of a colour.
ATTRIBUTES = {
    "bold": "\x1b[1m",
    "dim": "\x1b[2m",
    "italic": "\x1b[3m",
    "underline": "\x1b[4m",
    }
#* The colours, as the text's colour. ``highlight_<colour>`` is the same colour as its background.
#* The sequences are the ones termcolor writes (``orange`` is its (255, 165, 0)), so text made
#* with termcolor and with clitint is the same, byte for byte.
COLOURS = {
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
    "grey": "\x1b[90m",
    "orange": "\x1b[38;2;255;165;0m",
    "pink": "\x1b[38;2;255;192;203m",
    "purple": "\x1b[38;2;128;0;128m",
    "brown": "\x1b[38;2;165;42;42m",
    "teal": "\x1b[38;2;0;128;128m",
    "gold": "\x1b[38;2;255;215;0m",
    "maroon": "\x1b[38;2;128;0;0m",
    "navy": "\x1b[38;2;0;0;128m",
    "olive": "\x1b[38;2;128;128;0m",
    "coral": "\x1b[38;2;255;127;80m",
    "lime": "\x1b[38;2;0;255;0m",
    }
BACKGROUNDS = {
    "black": "\x1b[40m",
    "red": "\x1b[41m",
    "green": "\x1b[42m",
    "yellow": "\x1b[43m",
    "blue": "\x1b[44m",
    "magenta": "\x1b[45m",
    "cyan": "\x1b[46m",
    "white": "\x1b[47m",
    "grey": "\x1b[100m",
    "orange": "\x1b[48;2;255;165;0m",
    "pink": "\x1b[48;2;255;192;203m",
    "purple": "\x1b[48;2;128;0;128m",
    "brown": "\x1b[48;2;165;42;42m",
    "teal": "\x1b[48;2;0;128;128m",
    "gold": "\x1b[48;2;255;215;0m",
    "maroon": "\x1b[48;2;128;0;0m",
    "navy": "\x1b[48;2;0;0;128m",
    "olive": "\x1b[48;2;128;128;0m",
    "coral": "\x1b[48;2;255;127;80m",
    "lime": "\x1b[48;2;0;255;0m",
    }
RESET = "\x1b[0m"


#* What ``turn_colours_off`` or ``turn_colours_on`` chose, or None: the environment and the streams decide.
_CHOSEN: bool | None = None


def turn_colours_off() -> None:
    """Plain text from now on, whatever the environment and the streams say (as ``CLITINT_COLOURS_OFF=1``)."""
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
    Make ``name=1`` switch colours off too, as ``CLITINT_COLOURS_OFF=1`` does: for a library
    that offers its users a variable of its own (``add_off_switch("MYLIB_COLOURS_OFF")``). Only
    the value ``"1"`` counts. Asked with the other off switches, before ``FORCE_COLOR``.
    """
    global _OFF, _K_MORE
    if not isinstance(name, str) or not name:
        raise TypeError(f"an off switch is the name of an environment variable, not {name!r}")
    if name in _OFF:
        return
    _OFF = (*_OFF, name)
    if _ENV is not None:
        _K_MORE = (*_K_MORE, _encode_key(name))


def colours_on() -> bool:
    """
    Whether text is coloured now.

    A string doesn't know where it will end up: an uncaught error goes to stderr, ``print`` to
    stdout, a logger to a file. So colours are used only when both standard streams are
    terminals. Redirect either one (``2> errors.log``, ``| less``, a CI job) and text is plain:
    no escape sequence lands in a file.

    ``turn_colours_off`` and ``turn_colours_on`` decide before anything else. Then the
    environment, in this order: ``NO_COLOR`` (any value but an empty one, as no-color.org has it),
    ``ANSI_COLORS_DISABLED``, ``CLITINT_COLOURS_OFF=1`` (and each ``add_off_switch``) switch
    colours off, ``FORCE_COLOR`` (any value but an empty one, as force-color.org has it, ``0``
    included) switches them on whatever the streams are, and ``TERM=dumb`` switches them off.
    Read at every call, so a change takes effect at once. On Windows, the console is asked to
    show the sequences first; where it can't, text is plain.
    """
    if _CHOSEN is not None:                             # turn_colours_off / turn_colours_on: the program has said
        return _CHOSEN
    env = os.environ
    #* ``os.environ`` as it is now: a program may have put another mapping in its place. The one
    #* found at import keeps the same dictionary for good, so an identity test is enough (``getattr``
    #* and a type test each time cost 18 ns of 110).
    if env is not _ENV:
        if env.get(NO_COLOR) or ANSI_COLORS_DISABLED in env:
            return False
        for name in _OFF:
            if env.get(name) == "1":
                return False
        if env.get(FORCE_COLOR):
            return _CONSOLE is not None or _console_ready(True)
        if env.get(TERM) == "dumb":
            return False
        return _both_terminals()
    data = _DATA
    if data.get(_K_NO_COLOR) or _K_ANSI in data:      # an empty value is no value (b"" is falsy)
        return False
    #* clitint's own off switch alone, without a loop (12 ns); those of ``add_off_switch`` after it.
    if data.get(_K_OFF) == _V_ONE:
        return False
    if _K_MORE:
        for key in _K_MORE:
            if data.get(key) == _V_ONE:
                return False
    if data.get(_K_FORCE):                             #* the console asked once (Windows): no call after that
        return _CONSOLE is not None or _console_ready(True)
    if data.get(_K_TERM) == _V_DUMB:
        return False
    return _both_terminals()


#* ``os.environ`` encodes the name at every lookup and decodes the value: five of them took 1 µs.
#* Below it is the dictionary it keeps, which is asked directly, with the names and the two
#* values encoded once, the way ``os.environ`` does it on this platform. It is the same data:
#* what ``os.environ`` is given lands there. Where a Python has no such dictionary (it is a
#* CPython detail), ``os.environ`` is asked as usual.
#* The variables that switch colours off with the value "1": clitint's own, then each ``add_off_switch``
#* (``_K_OFF`` and ``_K_MORE`` encoded).
_OFF: tuple[str, ...] = (COLOURS_OFF,)
_K_MORE: tuple[Any, ...] = ()
#* The ``os.environ`` whose dictionary (``_DATA``) is read directly, or None: ask ``os.environ`` itself.
_ENV: Any = None
_DATA: dict[Any, Any] = {}
try:
    _encode_key, _encode_value = os.environ.encodekey, os.environ.encodevalue
    _K_OFF = _encode_key(COLOURS_OFF)
    _K_NO_COLOR, _K_ANSI, _K_FORCE, _K_TERM = (
        _encode_key(name) for name in (NO_COLOR, ANSI_COLORS_DISABLED, FORCE_COLOR, TERM)
        )
    _V_ONE, _V_DUMB = _encode_value("1"), _encode_value("dumb")
    if type(os.environ._data) is dict:                                              # type: ignore[attr-defined]
        _ENV, _DATA = os.environ, os.environ._data                                  # type: ignore[attr-defined]
except Exception:
    _ENV = None


#* (sys.stdout, sys.stderr, whether both are terminals): asked again only when a stream was replaced.
_streams: tuple[Any, Any, bool] = (None, None, False)


def _both_terminals() -> bool:
    global _streams
    out, err = sys.stdout, sys.stderr
    if _streams[0] is out and _streams[1] is err:
        return _streams[2]
    answer = _is_terminal(out) and _is_terminal(err) and _console_ready(False)
    _streams = (out, err, answer)
    return answer


def _is_terminal(stream: Any) -> bool:
    try:
        return bool(stream.isatty())
    except Exception:                   # no stream at all (pythonw), a closed one, an object without isatty
        return False


#* Whether the console shows escape sequences: None until asked (Windows only; True elsewhere).
_CONSOLE: bool | None = None if sys.platform == "win32" else True


def _console_ready(forced: bool) -> bool:
    """
    Whether the escape sequences will show as colours. On Windows 10 and 11 the console does
    that only once a program asks it to (``ENABLE_VIRTUAL_TERMINAL_PROCESSING``), so it is
    asked, once, for both streams. Where it refuses (an old console, no console), text is
    plain; unless colours were forced, which says the reader knows best (a CI log, a pipe to a
    viewer).
    """
    global _CONSOLE
    if _CONSOLE is None:
        _CONSOLE = _enable_windows_sequences()
    return _CONSOLE or forced


def _enable_windows_sequences() -> bool:
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        return _enable_sequences(ctypes.windll.kernel32)
    except Exception:                                   # no ctypes, no console: plain text
        return False


#* What GetStdHandle takes for stdout and stderr, and the console mode that reads escape sequences.
_STD_HANDLES = (-11, -12)
_VIRTUAL_TERMINAL = 0x0004


def _enable_sequences(kernel32: Any) -> bool:
    """
    Ask the Windows console behind stdout and stderr to read escape sequences, through
    ``kernel32`` (``ctypes.windll.kernel32``; a parameter so that it can be tried anywhere).
    True when every stream that is a console now reads them, or already did.
    """
    import ctypes
    done = False
    for which in _STD_HANDLES:
        handle = kernel32.GetStdHandle(which)
        if not handle or handle == -1:
            continue
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            continue                                    # no console (a file, a pipe): nothing to switch on
        if mode.value & _VIRTUAL_TERMINAL:
            done = True
            continue
        if not kernel32.SetConsoleMode(handle, mode.value | _VIRTUAL_TERMINAL):
            return False
        done = True
    return done


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
        if name == "highlight" and i + 1 < len(names) and names[i + 1] in BACKGROUNDS:
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
                raise ValueError(f"two colours in {spec!r}: name one, and 'highlight_<colour>' for a background")
            colour = COLOURS[name]
        else:
            raise ValueError(
                f"unknown style {name!r} in {spec!r}: a spec is made of {', '.join(ATTRIBUTES)}, "
                f"{', '.join(COLOURS)} and highlight_<colour>, joined by '_'"
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
            ``"underline_white_highlight_blue"``. Attributes: ``bold``, ``dim``, ``italic``,
            ``underline``. Colours: ``black``, ``red``, ``green``, ``yellow``, ``blue``,
            ``magenta``, ``cyan``, ``white``, ``grey``, ``orange``, ``pink``, ``purple``,
            ``brown``, ``teal``, ``gold``, ``maroon``, ``navy``, ``olive``, ``coral``,
            ``lime``; ``highlight_<colour>`` is a background. Anything else is a ``ValueError``.

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
    return f"{escapes[0]}{str(text)}{escapes[1]}"         #* one string made: ``a + t + b`` copied a long text twice


def escapes(*specs: str) -> tuple[str, ...]:
    """
    What is written in front of and behind a text for each of ``specs``, in one flat tuple:
    ``before, after, before, after ...``. For a message put together in one f-string, with the
    sequences as constants: cheaper than a ``formatter`` call per coloured word. Always the
    sequences, whatever ``colours_on`` says: the caller decides (``coloured()``).
    """
    return tuple([part for spec in specs for part in _escapes(spec)])


#* The pattern of a colour code, compiled at the first ``strip_colours``.
_ANSI: re.Pattern[str] | None = None


def strip_colours(text: str) -> str:
    """``text`` without its colours: every ANSI style sequence taken out, the words left as they are."""
    global _ANSI
    if _ANSI is None:
        import re
        _ANSI = re.compile(r"\x1b\[[0-9;]*m")
    return _ANSI.sub("", text)
