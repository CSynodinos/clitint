from __future__ import annotations
import os
import sys


TYPE_CHECKING = False
if TYPE_CHECKING:
    import re
    from types import MappingProxyType
    from typing import Any
else:
    MappingProxyType = type(type.__dict__)          #* `types.MappingProxyType`, without importing `types`


COLOURS_OFF = "CLITINT_COLOURS_OFF"
NO_COLOR = "NO_COLOR"
ANSI_COLORS_DISABLED = "ANSI_COLORS_DISABLED"
FORCE_COLOR = "FORCE_COLOR"
TERM = "TERM"

#* Spec: the tables kept here, and read-only views of them below (`ATTRIBUTES`, `COLOURS`, `BACKGROUNDS`).
_ATTRIBUTES = {
    "bold": "\x1b[1m",
    "dim": "\x1b[2m",
    "italic": "\x1b[3m",
    "underline": "\x1b[4m",
    }
_COLOURS = {
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
_BACKGROUNDS = {
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
ESC = "\x1b[0m"

#* What a program reads; `create_colour` is the one way in.
ATTRIBUTES: MappingProxyType[str, str] = MappingProxyType(_ATTRIBUTES)
COLOURS: MappingProxyType[str, str] = MappingProxyType(_COLOURS)
BACKGROUNDS: MappingProxyType[str, str] = MappingProxyType(_BACKGROUNDS)


#* What `turn_colours_off` or `turn_colours_on` chose, or None: the environment and the streams decide.
_CHOSEN: bool | None = None

#* While one message is built: the answer of `colours_on` for all of it (None: ask each time).
_decided: bool | None = None


# Optimization for environment variable lookups: avoid repeated encoding/decoding.
# --------------------------------------------------------------------------------
# `os.environ` encodes the name at every lookup and decodes the value: five of them take 1 µs.
# Below it is the dictionary it keeps, which is asked directly, with the names and the two
# values encoded once, the way `os.environ` does it on this platform. It is the same data:
# what `os.environ` is given lands there. Where a Python has no such dictionary (it is a
# CPython detail), `os.environ` is asked as usual.
# The variables that switch colours off with the value "1": clitint's own, then each `add_off_switch`
# (`_K_OFF` and `_K_MORE` encoded).
_OFF: tuple[str, ...] = (COLOURS_OFF,)
_K_MORE: tuple[Any, ...] = ()
#* The `os.environ` whose dictionary (`_DATA`) is read directly, or None: ask `os.environ` itself.
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


def turn_colours_off() -> None:
    """Plain text from now on, whatever the environment and the streams say (as `CLITINT_COLOURS_OFF=1`)."""
    global _CHOSEN
    _CHOSEN = False


def turn_colours_on() -> None:
    """Coloured text from now on, also where it goes to no terminal (as `FORCE_COLOR`)."""
    global _CHOSEN
    _CHOSEN = True


def let_the_environment_decide() -> None:
    """Undo `turn_colours_off` / `turn_colours_on`: the environment and the streams decide again."""
    global _CHOSEN
    _CHOSEN = None


def add_off_switch(name: str) -> None:
    """
    Make `name=1` switch colours off too, as `CLITINT_COLOURS_OFF=1` does: for a library
    that offers its users a variable of its own (`add_off_switch("MYLIB_COLOURS_OFF")`). Only
    the value `"1"` counts. Asked with the other off switches, before `FORCE_COLOR`.

    Example:
        add_off_switch("MYLIB_COLOURS_OFF")
    """
    global _OFF, _K_MORE
    if not isinstance(name, str) or not name:
        raise TypeError(f"an off switch is the name of an environment variable, not {name!r}")
    if name in _OFF:
        return
    _OFF = (*_OFF, name)
    if _ENV is not None:
        _K_MORE = (*_K_MORE, _encode_key(name))
    return


def create_colour(name: str, red: int, green: int, blue: int) -> str:
    """
    Add an RGB colour under `name` to `COLOURS` and `BACKGROUNDS`, and return `name`: from
    then on it goes in a spec as any colour does, alone or as `highlight_<name>`. Asking for
    a name again with the same components does nothing, so two libraries can each create the
    colour they need; another colour under a name already taken is refused.

    The colour is a 24-bit sequence (`38;2;r;g;b`). Where the terminal does not seem to show
    those, the text is written plain, with one `TrueColourWarning` per process (see `formatter`).

    Args:
        name (str): The name to use in specs: a word without `_` (specs are split on it), not
            an attribute, not `highlight`, and not a colour already taken with other components.
        red, green, blue (int): 0 to 255.

    Raises:
        TypeError: `name` is not a string, or a component is not an int (`bool` included).
        ValueError: `name` is empty, has a `_`, is an attribute or `highlight`, is another
            colour already, or a component is out of range.

    Example:
        >>> steel = create_colour("steel", 70, 130, 180)
        >>> formatter("x", f"bold_{steel}")
        '\\x1b[1m\\x1b[38;2;70;130;180mx\\x1b[0m'
    """
    if not isinstance(name, str):
        raise TypeError(f"a colour name is a string, not {name!r}")
    if not name or "_" in name:
        raise ValueError(f"a colour name is a word without '_', not {name!r}")
    if name in _ATTRIBUTES or name == "highlight":
        raise ValueError(f"{name!r} is already a style")
    for component in (red, green, blue):
        if not isinstance(component, int) or isinstance(component, bool):
            raise TypeError(f"a colour component is an int, not {component!r}")
        if not 0 <= component <= 255:
            raise ValueError(f"a colour component is 0 to 255, not {component}")
    colour = f"\x1b[38;2;{red};{green};{blue}m"
    if name in _COLOURS:
        #* The same colour again: nothing to do. Another one would change specs worked out already.
        if _COLOURS[name] == colour:
            return name
        raise ValueError(f"{name!r} is already a style, another colour")
    _COLOURS[name] = colour
    _BACKGROUNDS[name] = f"\x1b[48;2;{red};{green};{blue}m"
    return name


def create_multiple_colours(colours: dict[str, tuple[int, int, int]]) -> tuple[str, ...]:
    """
    `create_colour` for each `name: (red, green, blue)` of `colours`, all or none: where one is
    refused, those it added before are taken out again and the error is raised (a colour
    that was there already stays).

    Args:
        colours (dict[str, tuple[int, int, int]]): The names, each with its three components.

    Returns:
        tuple[str, ...]: The names, in the order given.

    Raises:
        TypeError, ValueError: As `create_colour`; also `TypeError` where a value is not three components.

    Example:
        >>> steel, sand = create_multiple_colours({"steel": (70, 130, 180), "sand": (194, 178, 128)})
        >>> formatter("x", f"{steel}_highlight_{sand}")
        '\\x1b[38;2;70;130;180m\\x1b[48;2;194;178;128mx\\x1b[0m'
    """
    added: list[str] = []
    try:
        for name, rgb in colours.items():
            if not isinstance(rgb, tuple) or len(rgb) != 3:
                raise TypeError(f"a colour is three components (red, green, blue), not {rgb!r}")
            new = name not in _COLOURS
            create_colour(name, *rgb)
            if new:
                added.append(name)
    except BaseException:
        for name in added:
            del _COLOURS[name], _BACKGROUNDS[name]
        raise
    return tuple(colours)


def colours_on() -> bool:
    """
    Whether coloured text is enabled right now. Inside `one_decision` (or between `decide()`
    and `release()`), the answer kept there. Otherwise the first rule that applies decides:

        1. `turn_colours_off()` / `turn_colours_on()`, if the program called one (`let_the_environment_decide()` undoes it).
        2. Plain: `NO_COLOR` (any value but an empty one, as no-color.org has it), `ANSI_COLORS_DISABLED`,
            `CLITINT_COLOURS_OFF=1`, or the `NAME=1` of an `add_off_switch`.
        3. Coloured: `FORCE_COLOR` (any value but an empty one, as force-color.org has it, `0` included),
            whatever the streams are. On Windows, only if the console can show escape sequences.
        4. Plain: `TERM=dumb`.
        5. Otherwise coloured only when both stdout and stderr are terminals (so with `2> errors.log`
            the text is plain and no escape codes land in the log), and, on Windows, the console shows
            escape sequences (it is asked once, and switched to read them).

    The environment is read at every call, so a change takes effect at once.

    Example:
        Run on a terminal, `colours_on()` is True; with `python app.py > out.txt` it is False.
    """
    return _colours_now() if _decided is None else _decided


def _colours_now() -> bool:
    """
    The rules of `colours_on`, asked now, whatever answer is kept. `formatter`, `one_decision` and
    `decide` call this, not `colours_on`: the kept answer is tested once, in `formatter`, not twice
    (a second test cost 15 ns of 135). To count or fix the answers in a test, patch this one.
    """
    if _CHOSEN is not None:                           # turn_colours_off / turn_colours_on: the program has said
        return _CHOSEN
    env = os.environ
    #* `os.environ` as it is now: a program may have put another mapping in its place. The one
    #* found at import keeps the same dictionary for good, so an identity test is enough (`getattr`
    #* and a type test each time cost 18 ns of 110).
    if env is not _ENV:
        if env.get(NO_COLOR) or ANSI_COLORS_DISABLED in env:
            return False
        for name in _OFF:
            if env.get(name) == "1":
                return False
        if env.get(FORCE_COLOR):
            return _CONSOLE_SHOWS_ESCAPES is not None or _win32_console_ready(True)
        if env.get(TERM) == "dumb":
            return False
        return _are_streams_terminals()
    data = _DATA
    if data.get(_K_NO_COLOR) or _K_ANSI in data:      # an empty value is no value (b"" is falsy)
        return False
    #* clitint's own off switch alone, without a loop (12 ns); those of `add_off_switch` after it.
    if data.get(_K_OFF) == _V_ONE:
        return False
    if _K_MORE:
        for key in _K_MORE:
            if data.get(key) == _V_ONE:
                return False
    if data.get(_K_FORCE):                             #* the console asked once (Windows): no call after that
        return _CONSOLE_SHOWS_ESCAPES is not None or _win32_console_ready(True)
    if data.get(_K_TERM) == _V_DUMB:
        return False
    return _are_streams_terminals()


#* (sys.stdout, sys.stderr, whether both are terminals): asked again only when a stream was replaced.
_std_streams: tuple[Any, Any, bool] = (None, None, False)


def _are_streams_terminals() -> bool:
    global _std_streams
    out, err = sys.stdout, sys.stderr
    if _std_streams[0] is out and _std_streams[1] is err:
        return _std_streams[2]
    answer = _is_a_terminal(out) and _is_a_terminal(err) and _win32_console_ready(False)
    _std_streams = (out, err, answer)
    return answer


def _is_a_terminal(stream: Any) -> bool:
    try:
        return bool(stream.isatty())
    except Exception:           # no stream at all (pythonw), a closed one, an object without isatty
        return False


#* Whether the console shows escape sequences: None until asked (Windows only; True elsewhere).
_CONSOLE_SHOWS_ESCAPES: bool | None = None if sys.platform == "win32" else True


def _win32_console_ready(forced: bool) -> bool:
    """
    Whether the escape sequences will show as colours. On Windows 10 and 11 the console does
    that only once a program asks it to (`ENABLE_VIRTUAL_TERMINAL_PROCESSING`), so it is
    asked, once, for both streams. Where it refuses (an old console, no console), text is
    plain; unless colours were forced, which says the reader knows best (a CI log, a pipe to a
    viewer).
    """
    global _CONSOLE_SHOWS_ESCAPES
    if _CONSOLE_SHOWS_ESCAPES is None:
        _CONSOLE_SHOWS_ESCAPES = _enable_windows_sequences()
    return _CONSOLE_SHOWS_ESCAPES or forced


def _enable_windows_sequences() -> bool:
    """Windows compatibility: enable virtual terminal sequences for the console."""
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        return _win32_sequences_compat_api(ctypes.windll.kernel32)
    except Exception:                                   # no ctypes, no console: plain text
        return False


#* What GetStdHandle takes for stdout and stderr, and the console mode that reads escape sequences.
_STD_HANDLES = (-11, -12)
_VIRTUAL_TERMINAL = 0x0004
def _win32_sequences_compat_api(kernel32: Any) -> bool:
    """
    Ask the Windows console behind stdout and stderr to read escape sequences, through
    `kernel32` (`ctypes.windll.kernel32`; a parameter so that it can be tried anywhere).
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


def decide() -> bool:
    """
    Ask `colours_on` now, keep the answer until `release()` (each `formatter` and `colours_on`
    gives it), and return it. A second `decide` asks again.
    """
    global _decided
    _decided = answer = _colours_now()
    return answer


def decision() -> bool | None:
    """The answer `decide` kept, or None where nothing has been decided."""
    return _decided


def release() -> None:
    """Forget the answer `decide` kept: each call asks `colours_on` again."""
    global _decided
    _decided = None


class one_decision:
    """
    Decide once whether colours are on, for everything built inside the block: each `formatter`
    and `colours_on` gives that answer, without reading the environment again. `as` gives it too.
    An inner block keeps the outer answer. Not for threads building messages at once: the answer
    is kept in the module.

    Example:
        with one_decision() as on:
            line = formatter("Hello", "red") + " " + formatter("World", "green")

    Something that would change the answer inside the block, such as `turn_colours_off()`,
    counts only after it:

        with one_decision():
            turn_colours_off()
            formatter("x", "red")       # still coloured: decided at the start of the block
        formatter("x", "red")           # 'x'
    """
    __slots__ = ("_outer",)

    def __enter__(self) -> bool:
        global _decided
        self._outer = _decided
        if _decided is None:
            _decided = _colours_now()
        return _decided

    def __exit__(self, *_: Any) -> None:
        global _decided
        _decided = self._outer
        return


def _escapes(spec: str) -> tuple[str, str]:
    """
    Add escapes for `spec`:

    * The attributes sequences
    * Colour
    * Background
    * Escape sequence that resets all styles

    Returns:
        tuple[str, str]: The escape sequences for the given `spec` and the reset sequence.
    """
    attributes: list[str] = []
    colour = background = ""
    names = spec.split("_")
    i = 0
    while i < len(names):
        name = names[i]
        if name == "highlight" and i + 1 < len(names) and names[i + 1] in _BACKGROUNDS:
            if background:
                raise ValueError(f"two backgrounds in {spec!r}")
            background = _BACKGROUNDS[names[i + 1]]
            i += 2
            continue
        if name in _ATTRIBUTES:
            if _ATTRIBUTES[name] not in attributes:
                attributes.append(_ATTRIBUTES[name])
        elif name in _COLOURS:
            if colour and colour != _COLOURS[name]:
                raise ValueError(f"two colours in {spec!r}: name one, and 'highlight_<colour>' for a background")
            colour = _COLOURS[name]
        else:
            raise ValueError(
                f"unknown style {name!r} in {spec!r}: a spec is made of {', '.join(_ATTRIBUTES)}, "
                f"{', '.join(_COLOURS)} and highlight_<colour>, joined by '_'"
                )
        i += 1
    order = list(_ATTRIBUTES.values())
    attributes.sort(key = order.index)
    return "".join(attributes) + colour + background, ESC


#* spec -> what `_escapes` answered: the specs of the colours every terminal shows (the hot path),
#* and those with a 24-bit colour (`38;2;` / `48;2;`), which are asked whether the terminal shows them.
_ESCAPES: dict[str, tuple[str, str]] = {}
_RGB_ESCAPES: dict[str, tuple[str, str]] = {}


class TrueColourWarning(RuntimeWarning):
    """A spec has a 24-bit colour and the terminal does not seem to show those: the text is plain."""


#* Whether the terminal shows 24-bit colour: None until a 24-bit spec is first written.
_SHOWS_RGB: bool | None = None
_warned = False
_RGB_PROGRAMS = ("iTerm.app", "vscode", "WezTerm", "ghostty", "Hyper", "Tabby")
_RGB_TERMS = ("-direct", "kitty", "alacritty", "ghostty", "wezterm", "foot", "truecolor", "24bit")


def _terminal_shows_rgb() -> bool:
    """
    Whether the terminal shows 24-bit colour, as far as it can be told: `COLORTERM=truecolor`
    (or `24bit`), the convention; or a terminal known to (Windows Terminal, a `TERM_PROGRAM` or
    `TERM` of one); or, on Windows, a console that took the escape sequences.
    """
    env = os.environ
    if env.get("COLORTERM", "").lower() in ("truecolor", "24bit") or env.get("WT_SESSION"):
        return True
    if env.get("TERM_PROGRAM", "") in _RGB_PROGRAMS:
        return True
    term = env.get("TERM", "").lower()
    if any(name in term for name in _RGB_TERMS):
        return True
    return sys.platform == "win32" and bool(_CONSOLE_SHOWS_ESCAPES)


def _shows_rgb(spec: str) -> bool:
    """Whether to write the 24-bit `spec`: always where colours are forced; else as the terminal says, with one warning."""
    global _SHOWS_RGB, _warned
    if _CHOSEN or os.environ.get(FORCE_COLOR):        #* forced: the reader knows best (a CI log, a viewer)
        return True
    if _SHOWS_RGB is None:
        _SHOWS_RGB = _terminal_shows_rgb()
    if not _SHOWS_RGB and not _warned:
        _warned = True
        import warnings
        warnings.warn(
            f"the terminal does not seem to show 24-bit colour ({spec!r}): such text is written plain. "
            "Set COLORTERM=truecolor or FORCE_COLOR=1 if it does",
            TrueColourWarning, stacklevel = 4,
            )
    return _SHOWS_RGB


def _format_new(txt: str, spec: str) -> str:
    """`formatter` for a spec not in `_ESCAPES`: one seen for the first time, or one with a 24-bit colour."""
    escapes = _RGB_ESCAPES.get(spec)
    if escapes is None:
        escapes = _escapes(spec)
        if "8;2;" not in escapes[0]:
            _ESCAPES[spec] = escapes
            return f"{escapes[0]}{txt}{escapes[1]}"
        _RGB_ESCAPES[spec] = escapes
    if not _shows_rgb(spec):
        return txt
    return f"{escapes[0]}{txt}{escapes[1]}"


def formatter(text: Any, spec: str) -> str:
    """
    Format `text` with the given style `spec` if colours are on.

    Args:
        text (Any): The text, or any object: its `str` is what is written.
        spec (str): Styles joined by `_`, in any order.

    Returns:
        str: The text between the escape sequences of its styles, or the plain text.

    A spec is made of the names of `ATTRIBUTES`, at most one of `COLOURS`, and at most one
    `highlight_<colour>` (a name of `BACKGROUNDS`). A 24-bit colour (`orange` and those after it,
    and those of `create_colour`) is written only where the terminal seems to show it, or where
    colours are forced; elsewhere the text is plain, with one `TrueColourWarning` per process.

    Example:
        >>> formatter("hello", "bold_red")
        '\\x1b[1m\\x1b[31mhello\\x1b[0m'
    """
    txt = str(text)
    if not (_colours_now() if _decided is None else _decided):
        return txt
    escapes = _ESCAPES.get(spec)
    if escapes is None:
        return _format_new(txt, spec)
    return f"{escapes[0]}{txt}{escapes[1]}"         #* one string made: `a + t + b` copied a long text twice


def escapes(*specs: str) -> tuple[str, ...]:
    """
    What is written in front of and behind a text for each of `specs`, in one flat tuple:
    `before, after, before, after ...`.

    Args:
        *specs (str): Styles joined by `_`, in any order.

    Returns:
        tuple[str, ...]: The escape sequences for each spec, in the order given.

    Example:
        >>> escapes("bold_red", "underline_blue")
        ('\\x1b[1m\\x1b[31m', '\\x1b[0m', '\\x1b[4m\\x1b[34m', '\\x1b[0m')
    """
    return tuple([part for spec in specs for part in _escapes(spec)])


#* The pattern of a colour code, compiled at the first `strip_colours`.
_ANSI: re.Pattern[str] | None = None


def strip_colours(text: str) -> str:
    """Remove all ANSI formatting from `text` and return a new string object."""
    global _ANSI
    if _ANSI is None:
        import re
        _ANSI = re.compile(r"\x1b\[[0-9;]*m")
    return _ANSI.sub("", text)
