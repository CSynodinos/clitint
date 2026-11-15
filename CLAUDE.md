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
  `underline`, `black`, `white`, `grey`, and backgrounds `highlight_<colour>`. Two colours or two backgrounds in a spec are
  a `ValueError`.
- `let_the_environment_decide()` undoes `turn_colours_off` / `turn_colours_on`.
- For a library built on it: `add_off_switch(name)` (its own `NAME=1`), and `decide()` / `decision()` / `release()`,
  the fast form of `one_decision` (which nests: an inner one keeps the outer answer).

## Commands

```bash
~/venvs/clitint/bin/python -m pytest -q          # 3.14; ~/venvs/clitint_3.13 for 3.13. Both must pass
~/venvs/clitint/bin/python -m mypy --strict clitint
~/venvs/clitint/bin/python -m build              # wheel + sdist
pip install -e ".[dev]" --config-settings editable_mode=compat   # to make a venv again (compat: mypy sees it)
```

The project lives in `/mnt/d/dev/clitint`, in its own git repository (moved out of enforced's `prototypes/` on
2026-11-15). Also used by cfgcast (`formatter`, the two switches).
The name `termtint` was taken on PyPI (another project, hasheramin5-cyber/TermTint): hence clitint.

## Layout

```
clitint/__init__.py   the public names, __version__ (pyproject reads it)
clitint/_tint.py      everything: the style tables, colours_on, formatter, escapes, one_decision, strip_colours
tests/test_tint.py     one file: specs, stripping, one decision, when text is coloured
```

## How it works

- `formatter(text, spec)` asks `colours_on()` (or the decision `one_decision` made), then the sequences of the spec
  from `_ESCAPES`, worked out once per spec by `_escapes` (attributes in table order, then colour, then background).
- `colours_on` reads the dictionary below `os.environ` (`os.environ._data`, the names encoded once): five lookups
  through `os.environ` cost 1 µs. Read from `os.environ` at each call, so a mapping put in its place is seen, and
  `os.environ` itself is asked where there is no such dictionary (`_FAST`). A CPython detail, accepted.
- Whether the streams are terminals is remembered until `sys.stdout` or `sys.stderr` is replaced (`_streams`).
- `one_decision` keeps one answer in a module global while a message is built: not for threads building messages
  at once (said in its docstring).

## Rules

Keep it dependency-free and small; tests for every behaviour; mypy `--strict` clean; style as enforced's (4-space
indent, `x = y` spacing, `#*` for important comments, docstrings on public functions, type hints everywhere).
Commit only when asked; no `git stash`.
