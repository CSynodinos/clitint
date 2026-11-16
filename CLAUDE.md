# clitint

Coloured terminal text for Python 3.13+, no dependencies: `from clitint import formatter`. Text is coloured only
when both stdout and stderr are terminals (or the environment / the program says otherwise), so no escape sequence
lands in a file.

It is enforced's `_formatting_tool.py` made a project of its own (2026-11-15, the owner's decision; enforced is
`/mnt/d/dev/enforced`), and **enforced's one dependency** from its next release (`clitint>=0.1.0`). Each enforced module
imports what it uses from clitint directly; enforced has no colour variable of its own (its users set `CLITINT_COLOURS_OFF`), exports `turn_colours_off` / `turn_colours_on`, and uses
`decide` / `decision` / `release` around a message. Its tests compare whole coloured messages byte for byte, and
some patch `clitint._tint` (`_CHOSEN`, `colours_on`): **a change here is a change to enforced**, so run enforced's
pytest and simulation too (`~/venvs/python_validate_3.14` and `_3.13` have clitint installed editable from here).

What differs from enforced's copy:
- The off switch is `CLITINT_COLOURS_OFF=1` (enforced had `ENFORCED_COLOURS_OFF`; gone, enforced follows clitint).
  `NO_COLOR` and `FORCE_COLOR` count when not empty (no-color.org, force-color.org; enforced's copy took any value,
  2026-11-15). On Windows the console is switched to read escape sequences (`_console_ready`, `_enable_sequences`,
  once, both streams); where it refuses, plain unless forced. Tried with a stand-in kernel32: no Windows machine here.
- More styles: enforced has only those its messages use (bold and seven colours). Here also `dim`, `italic`,
  `underline`, `black`, `white`, `grey`, eleven 24-bit colours (`orange` ... `lime`), backgrounds `highlight_<colour>`,
  and `create_colour(name, r, g, b)` (a 24-bit colour under a new name, in `COLOURS` and `BACKGROUNDS`; returns the
  name), `create_multiple_colours({name: (r, g, b)})` (all or none). Two colours or two backgrounds in a spec are a `ValueError`. No check for 24-bit support (none is reliable).
- `let_the_environment_decide()` undoes `turn_colours_off` / `turn_colours_on`.
- For a library built on it: `add_off_switch(name)` (its own `NAME=1`), and `decide()` / `decision()` / `release()`,
  the fast form of `one_decision` (which nests: an inner one keeps the outer answer).

## Commands

```bash
~/venvs/clitint/bin/python -m pytest -q          # 3.14; ~/venvs/clitint_3.13 for 3.13. Both must pass
~/venvs/clitint/bin/python -m mypy --strict clitint
~/venvs/clitint/bin/python -m build              # wheel + sdist
~/venvs/clitint/bin/python -m mypy --strict --platform win32 clitint   # the Windows branch too
pip install -e ".[dev]" --config-settings editable_mode=compat   # to make a venv again (compat: mypy sees it)
bash publish.sh --test-env                       # build, twine check, TestPyPI (as enforced's)
python benchmarks/compare.py                     # clitint vs TermTint vs termcolor: the tables of COMPARISON.md
```

`benchmarks/compare.py` needs `termtint` and `termcolor` installed next to clitint, *not* editable (all three from
the same disk): the run of 2026-11-15 used a throwaway venv with `pip install termtint termcolor /mnt/d/dev/clitint`.
It checks that the three print the same visible text before timing, runs each case in a fresh interpreter, and
checks behaviour with real pseudo-terminals. After a change on the hot path, run it and update
`benchmarks/COMPARISON.md` (numbers, and any sentence they contradict).

## Layout

```
clitint/__init__.py   the public names, __version__ (pyproject reads it)
clitint/_tint.py      everything: the style tables, colours_on, formatter, escapes, one_decision, strip_colours
tests/test_tint.py    one file: specs, stripping, one decision, when text is coloured, Windows, imports
benchmarks/           compare.py and COMPARISON.md (the comparison with TermTint and termcolor)
docs/                 example.svg (the README's picture)
publish.sh, env.sh    upload to (Test)PyPI; the venv. tokens (git-ignored) is the owner's: never read it
```

## How it works

- `formatter(text, spec)` asks `colours_on()` (or the decision `one_decision` made), then the sequences of the spec
  from `_ESCAPES`, worked out once per spec by `_escapes` (attributes in table order, then colour, then background),
  and makes the result as one f-string: `before + text + after` copied a long text twice (100 KB: 1.8 µs, termcolor
  1.0).
- **Nothing but `os` and `sys` at import** (2026-11-15): `typing`, with `re` inside it, was 3.4 ms of a 4.1 ms start
  (termcolor: 1.5). `from __future__ import annotations` and `TYPE_CHECKING = False` (the name, not `typing`'s) keep
  annotations as text; `strip_colours` imports `re` and compiles `_ANSI` at its first call.
  `test_importing_loads_neither_typing_nor_re` holds it.
- `colours_on` reads the dictionary below `os.environ` (`os.environ._data`, the names encoded once): five lookups
  through `os.environ` cost 1 µs. The `os.environ` found at import and its dictionary are kept (`_ENV`, `_DATA`):
  that object keeps the same dictionary for good, so each call only asks `os.environ is _ENV` (a mapping put in its
  place is seen, and asked as a mapping). `_ENV` is None where there is no such dictionary. A CPython detail, accepted.
  clitint's own off switch is tested on its own (`_K_OFF`); only `add_off_switch` names go through a loop (`_K_MORE`).
- Whether the streams are terminals is remembered until `sys.stdout` or `sys.stderr` is replaced (`_streams`).
- The check reads the environment at every call (92 ns with colours forced, 38 with `NO_COLOR` in compare.py, against termcolor's
  12 and TermTint's 64, which keep their first answer): that is what lets it see `NO_COLOR` set while a program runs,
  and `one_decision` is how a batch pays it once. Don't cache it.
  Trimmed on 2026-11-15, each step timed first (the owner: "only implement if worth it"). Kept: the identity test
  (-18 ns) and the single off switch (-12). Turned down: `key in data and data[key]` in place of `.get` (5-10 ns
  less with nothing set, 8-11 more with `NO_COLOR` set: the CI and log case) and the check written into `formatter`
  (no faster than calling it, sometimes slower, and two copies). Inlining the stream check: not worth its complexity.
- `one_decision` keeps one answer in a module global while a message is built: not for threads building messages
  at once (said in its docstring).

## Rules

Keep it dependency-free and small; nothing imported at run time beyond `os` and `sys` (`ctypes` on Windows, when
the console is asked); tests for every behaviour; mypy `--strict` clean; style as enforced's (4-space
indent, `x = y` spacing, `#*` for important comments, docstrings on public functions, type hints everywhere).
Commit only when asked; no `git stash`.
