from clitint import formatter, strip_colours, escapes, one_decision, coloured
from typing import Any
import clitint
import clitint._tint as tint
import subprocess
import sys
import os
import pytest


@pytest.fixture(autouse = True)
def colours_wanted(monkeypatch):
    """
    Most tests are about what a spec is turned into, so they need colours on: whatever the shell
    exports, and although pytest's captured output is no terminal.
    """
    for name in ("CLITINT_COLOURS_OFF", "NO_COLOR", "ANSI_COLORS_DISABLED"):
        monkeypatch.delenv(name, raising = False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setattr(tint, "_CHOSEN", None)
    monkeypatch.setattr(tint, "_decided", None)


#* The escape sequences, written out here a second time: what a terminal is to be sent.
CODES = {"bold": "\x1b[1m", "dim": "\x1b[2m", "italic": "\x1b[3m", "underline": "\x1b[4m",
         "black": "\x1b[30m", "red": "\x1b[31m", "green": "\x1b[32m", "yellow": "\x1b[33m", "blue": "\x1b[34m",
         "magenta": "\x1b[35m", "cyan": "\x1b[36m", "white": "\x1b[37m", "grey": "\x1b[90m",
         "orange": "\x1b[38;2;255;165;0m"}
BACK = {"black": "\x1b[40m", "red": "\x1b[41m", "green": "\x1b[42m", "yellow": "\x1b[43m", "blue": "\x1b[44m",
        "magenta": "\x1b[45m", "cyan": "\x1b[46m", "white": "\x1b[47m", "grey": "\x1b[100m",
        "orange": "\x1b[48;2;255;165;0m"}
COLOURS = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "grey", "orange"]
ATTRS = ["bold", "dim", "italic", "underline"]


def styled(text: str, color: Any = None, attrs: Any = (), on: Any = None) -> str:
    """``text`` as ``formatter`` has to return it: attributes, colour, background, and a reset behind."""
    return ("".join(CODES[attr] for attr in attrs) + (CODES[color] if color else "") + (BACK[on] if on else "")
            + text + "\x1b[0m")


# ═════════════════════════════════════════════════════════════════════════════
#  WHAT A SPEC IS TURNED INTO
# ═════════════════════════════════════════════════════════════════════════════

class TestFormatter:

    def test_returns_the_text_between_the_sequences(self):
        assert formatter("hello", "red") == "\x1b[31mhello\x1b[0m"
        assert formatter("hello", "bold_red") == "\x1b[1m\x1b[31mhello\x1b[0m"
        assert formatter("hello", "bold") == "\x1b[1mhello\x1b[0m"

    def test_the_tables_are_the_sequences_written_here(self):
        assert clitint.ATTRIBUTES | clitint.COLOURS == CODES
        assert clitint.BACKGROUNDS == BACK

    @pytest.mark.parametrize("color", COLOURS)
    def test_each_colour_alone_with_each_attribute_and_as_a_background(self, color):
        assert formatter("text", color) == styled("text", color)
        for attr in ATTRS:
            assert formatter("text", f"{attr}_{color}") == styled("text", color, [attr])
        assert formatter("text", f"highlight_{color}") == styled("text", on = color)
        assert formatter("text", f"bold_white_highlight_{color}") == styled("text", "white", ["bold"], color)

    @pytest.mark.parametrize("color", COLOURS)
    def test_the_order_in_a_spec_does_not_matter(self, color):
        expected = styled("t", color, ["bold", "underline"], "blue")
        for spec in (f"bold_underline_{color}_highlight_blue", f"highlight_blue_{color}_underline_bold", f"underline_highlight_blue_bold_{color}"):
            assert formatter("t", spec) == expected

    def test_a_style_named_twice_is_written_once(self):
        assert formatter("t", "bold_red_bold_red") == styled("t", "red", ["bold"])

    # --- text variants ---

    def test_empty_text(self):
        assert formatter("", "red") == styled("", "red")

    def test_text_with_special_characters(self):
        assert formatter("hi\nthere", "red") == styled("hi\nthere", "red")

    @pytest.mark.parametrize("text", [5, 2.5, None, ("a", 1), ["x"], b"raw", ValueError("no")], ids = repr)
    def test_text_that_is_no_string(self, text):
        assert formatter(text, "bold_red") == styled(str(text), "red", ["bold"])

    @pytest.mark.parametrize("text", ["\x1b[31mred\x1b[0m", "%d %s", "{0}", "\x00x\x00", "a\x00b"])
    def test_text_is_never_read_as_anything_else(self, text):
        assert formatter(text, "bold_green") == styled(text, "green", ["bold"])

    # --- what there is no style for ---

    @pytest.mark.parametrize("spec", ["purple", "", "bold_purple", "highlight", "highlight_bold", "light_red", "teal", "red_highlight", "on_blue"])
    def test_an_unknown_style_is_refused_by_name(self, spec):
        for _ in range(2):                                          # the refusal is not remembered as an answer
            with pytest.raises(ValueError, match = "unknown style"):
                formatter("text", spec)

    @pytest.mark.parametrize("spec, why", [("red_blue", "two colours"), ("highlight_red_highlight_blue", "two backgrounds")])
    def test_two_colours_or_two_backgrounds_are_refused(self, spec, why):
        with pytest.raises(ValueError, match = why):
            formatter("text", spec)

    def test_with_colours_off_the_spec_is_not_read(self, monkeypatch):
        monkeypatch.setenv("CLITINT_COLOURS_OFF", "1")
        assert formatter("text", "bold_red") == "text" and formatter(5, "purple") == "5"


def test_the_sequences_are_the_ones_termcolor_writes():
    #* Where termcolor happens to be installed: text is, to the byte, what it makes.
    termcolor = pytest.importorskip("termcolor")
    for color in COLOURS:
        name: Any = (255, 165, 0) if color == "orange" else ("light_grey" if color == "white" else color)
        if color in ("grey", "white"):
            continue                                                # termcolor's names for 90 / 37 changed across versions
        assert formatter("x", color) == termcolor.colored("x", name, force_color = True)
        assert formatter("x", f"bold_{color}") == termcolor.colored("x", name, attrs = ["bold"], force_color = True)
    assert formatter("x", "bold") == termcolor.colored("x", attrs = ["bold"], force_color = True)


def test_the_package_imports_nothing_but_the_standard_library():
    code = ("import sys; before = set(sys.modules); import clitint\n"
            "new = {name.split('.')[0] for name in set(sys.modules) - before}\n"
            "print(sorted(new - set(sys.stdlib_module_names) - {'clitint'}))")
    done = subprocess.run([sys.executable, "-c", code], capture_output = True, text = True)
    assert done.stdout.strip() == "[]", done.stdout + done.stderr


def test_a_spec_is_worked_out_once_not_once_per_text(monkeypatch):
    asked = []
    real = tint._escapes
    monkeypatch.setattr(tint, "_escapes", lambda spec: asked.append(spec) or real(spec))
    monkeypatch.setattr(tint, "_ESCAPES", {})
    texts = [formatter(word, "bold_yellow") for word in ("int", "str", "float")] + [formatter("x", "bold_red")]
    assert texts == [styled(w, "yellow", ["bold"]) for w in ("int", "str", "float")] + [styled("x", "red", ["bold"])]
    assert asked == ["bold_yellow", "bold_red"]


# ═════════════════════════════════════════════════════════════════════════════
#  STRIPPING, ESCAPES, ONE DECISION
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("spec", ["red", "bold_orange", "underline_white_highlight_grey", "highlight_orange"])
def test_strip_colours_gives_the_text_back(spec):
    assert strip_colours(formatter("a b\nc", spec)) == "a b\nc"
    assert strip_colours("plain") == "plain"
    assert strip_colours(formatter("x", "red") + " and " + formatter("y", "bold")) == "x and y"


def test_escapes_are_the_formatter_s_sequences_whatever_colours_say(monkeypatch):
    before, after, bold_before, bold_after = escapes("red", "bold")
    assert f"{before}x{after}" == formatter("x", "red") and f"{bold_before}x{bold_after}" == formatter("x", "bold")
    monkeypatch.setenv("CLITINT_COLOURS_OFF", "1")
    assert escapes("red") == ("\x1b[31m", "\x1b[0m")
    with pytest.raises(ValueError):
        escapes("purple")


def test_one_decision_asks_once_and_leaves_nothing_behind(monkeypatch):
    asked = []
    real = tint.colours_on
    monkeypatch.setattr(tint, "colours_on", lambda: asked.append(1) or real())
    with one_decision():
        words = [formatter(w, "bold") for w in "abcde"]
        assert coloured()
    assert len(asked) == 1 and all("\x1b[" in w for w in words)
    assert tint._decided is None
    monkeypatch.setenv("CLITINT_COLOURS_OFF", "1")
    with one_decision():
        assert formatter("x", "bold") == "x" and not coloured()


# ═════════════════════════════════════════════════════════════════════════════
#  WHEN TEXT IS COLOURED
# ═════════════════════════════════════════════════════════════════════════════

class _Stream:
    def __init__(self, terminal: bool) -> None:
        self.terminal = terminal

    def isatty(self) -> bool:
        return self.terminal

    def write(self, text: str) -> int:
        return len(text)

    def flush(self) -> None:
        pass


def _streams(monkeypatch, out: bool, err: bool) -> None:
    monkeypatch.delenv("FORCE_COLOR", raising = False)
    monkeypatch.delenv("TERM", raising = False)
    monkeypatch.setattr(sys, "stdout", _Stream(out))
    monkeypatch.setattr(sys, "stderr", _Stream(err))


@pytest.mark.parametrize("out, err, expected", [
    (True, True, True),             # a terminal: someone is reading
    (True, False, False),           # 2> errors.log
    (False, True, False),           # | less, > out.txt
    (False, False, False),          # a CI job, a service
    ])
def test_colours_need_both_streams_to_be_terminals(monkeypatch, out, err, expected):
    _streams(monkeypatch, out, err)
    assert clitint.colours_on() is expected
    assert (formatter("x", "bold") != "x") is expected


def test_the_environment_decides_before_the_streams(monkeypatch):
    _streams(monkeypatch, True, True)
    for name, value in (("CLITINT_COLOURS_OFF", "1"), ("NO_COLOR", "1"), ("ANSI_COLORS_DISABLED", "1"), ("TERM", "dumb")):
        monkeypatch.setenv(name, value)
        assert clitint.colours_on() is False, name
        monkeypatch.delenv(name)
    _streams(monkeypatch, False, False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert clitint.colours_on() is True
    monkeypatch.setenv("CLITINT_COLOURS_OFF", "1")           # off wins over forced
    assert clitint.colours_on() is False


def test_the_program_decides_before_the_environment(monkeypatch):
    _streams(monkeypatch, False, False)
    clitint.turn_colours_on()
    assert clitint.colours_on() and formatter("x", "red") == styled("x", "red")
    monkeypatch.setenv("FORCE_COLOR", "1")
    clitint.turn_colours_off()
    assert not clitint.colours_on() and formatter("x", "red") == "x"
    clitint.let_the_environment_decide()
    assert clitint.colours_on()                                # FORCE_COLOR again


def test_a_stream_without_isatty_is_no_terminal(monkeypatch):
    monkeypatch.delenv("FORCE_COLOR", raising = False)
    monkeypatch.setattr(sys, "stdout", None)                    # pythonw, a detached process
    monkeypatch.setattr(sys, "stderr", object())
    assert clitint.colours_on() is False and formatter("x", "red") == "x"


def test_the_environment_is_read_as_it_is_now(monkeypatch):
    #* colours_on reads the dictionary below os.environ. That is the same data, whichever way it is
    #* changed, and another mapping put in the place of os.environ is read as well.
    for name in ("CLITINT_COLOURS_OFF", "NO_COLOR", "ANSI_COLORS_DISABLED", "FORCE_COLOR", "TERM"):
        monkeypatch.delenv(name, raising = False)
    monkeypatch.setattr(tint, "_both_terminals", lambda: True)
    assert tint._FAST and tint.colours_on()
    steps = [("TERM", "dumb", False), ("FORCE_COLOR", "1", True), ("ANSI_COLORS_DISABLED", "", False)]
    for name, value, expected in steps:
        os.environ[name] = value
        assert tint.colours_on() is expected
    for name, _, _ in steps:
        del os.environ[name]
    assert tint.colours_on()
    os.environ.update({"CLITINT_COLOURS_OFF": "1"})
    assert not tint.colours_on()
    os.environ.pop("CLITINT_COLOURS_OFF")
    monkeypatch.setattr(os, "environ", {"NO_COLOR": "1"})           # a plain dictionary in its place
    assert not tint.colours_on()
    monkeypatch.setattr(os, "environ", {"TERM": "xterm"})
    assert tint.colours_on()
    monkeypatch.setattr(tint, "_FAST", False)                       # a Python without that dictionary: the same answers
    assert tint.colours_on()
    monkeypatch.setattr(os, "environ", {"TERM": "dumb"})
    assert not tint.colours_on()


def test_a_child_process_is_plain_when_piped_and_coloured_when_forced():
    code = "from clitint import formatter; print(repr(formatter('x', 'red')))"
    env = {k: v for k, v in os.environ.items() if k not in ("FORCE_COLOR", "NO_COLOR", "CLITINT_COLOURS_OFF")}
    piped = subprocess.run([sys.executable, "-c", code], capture_output = True, text = True, env = env)
    forced = subprocess.run([sys.executable, "-c", code], capture_output = True, text = True, env = env | {"FORCE_COLOR": "1"})
    assert piped.stdout.strip() == "'x'"
    assert forced.stdout.strip() == repr(styled("x", "red"))


# ═════════════════════════════════════════════════════════════════════════════
#  WHAT A LIBRARY BUILT ON CLITINT USES
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("fast", [True, False])
def test_an_off_switch_of_a_library_s_own(monkeypatch, fast):
    monkeypatch.setattr(tint, "_OFF", tint._OFF)
    monkeypatch.setattr(tint, "_K_OFFS", tint._K_OFFS)
    monkeypatch.setattr(tint, "_FAST", fast and tint._FAST)
    clitint.add_off_switch("MYLIB_COLOURS_OFF")
    clitint.add_off_switch("MYLIB_COLOURS_OFF")                    # twice is once
    assert tint._OFF == ("CLITINT_COLOURS_OFF", "MYLIB_COLOURS_OFF")
    assert clitint.colours_on()                                    # FORCE_COLOR, from the fixture
    for value, on in (("0", True), ("", True), ("yes", True), ("1", False)):
        monkeypatch.setenv("MYLIB_COLOURS_OFF", value)
        assert clitint.colours_on() is on, value                   # "1" and nothing else
    monkeypatch.setenv("CLITINT_COLOURS_OFF", "1")
    monkeypatch.delenv("MYLIB_COLOURS_OFF")
    assert not clitint.colours_on()                                # clitint's own still counts


@pytest.mark.parametrize("name", ["", None, 5])
def test_an_off_switch_is_a_name(name):
    with pytest.raises(TypeError):
        clitint.add_off_switch(name)


def test_decide_keeps_the_answer_until_release(monkeypatch):
    assert clitint.decision() is None
    assert clitint.decide() is True
    monkeypatch.setenv("CLITINT_COLOURS_OFF", "1")
    assert clitint.decision() is True and coloured() and formatter("x", "red") == styled("x", "red")
    clitint.release()
    assert clitint.decision() is None and formatter("x", "red") == "x"


def test_one_decision_inside_another_keeps_the_outer_answer(monkeypatch):
    with one_decision() as outer:
        monkeypatch.setenv("CLITINT_COLOURS_OFF", "1")
        with one_decision() as inner:
            assert outer is inner is True
        assert clitint.decision() is True                          # the inner one left it in place
    assert clitint.decision() is None
