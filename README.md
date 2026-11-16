<div align="center">

# clitint

**Very fast terminal text formatting for Python 3.13+, with no dependencies.**

![Python](https://img.shields.io/badge/python-3.13%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![Typed](https://img.shields.io/badge/mypy-strict-informational)
![Licence](https://img.shields.io/badge/licence-MIT-lightgrey)


Text is coloured only when someone is reading it on a terminal: redirect the output to a file, a pipe or a CI log
and it comes out plain.

This library is ideal for simple and very fast formatting of text on libraries and command-line tools.

```python
from clitint import formatter

text_1 = formatter("error:", "bold_red")
text_2 = formatter("warning", "underline_black_highlight_yellow")
print(text_1, "file not found")
print(text_2)
```

</div>
<img src="https://raw.githubusercontent.com/CSynodinos/clitint/main/docs/example.svg" alt="clitint printing a bold red 'error:' and an underlined black-on-yellow 'warning' in a terminal, and plain text when redirected to a file" width="640">

</div>


It is made for libraries and tools that build messages: one call with a short spec, an answer that follows the
environment as it is now, and colours only when **both** stdout and stderr are terminals, so an error message that
ends up in a log has no escape codes in it.

> [!NOTE]
> For 256-colour palettes or themes, use another library.

## 📦 Install

```bash
pip install clitint
```

## 🎨 Specs

A spec is a set of styles joined by `_`, in any order: `"red"`, `"bold_red"`, `"red_bold"`,
`"italic_white_highlight_blue"`.

| Kind        | Names                                                                                    |
|-------------|------------------------------------------------------------------------------------------|
| Attributes  | `bold` `dim` `italic` `underline`                                                        |
| Colours     | `black` `red` `green` `yellow` `blue` `magenta` `cyan` `white` `grey` `orange` `pink` `purple` `brown` `teal` `gold` `maroon` `navy` `olive` `coral` `lime` |
| Backgrounds | `highlight_` followed by a colour, e.g. `highlight_blue`                                 |

Combine as many attributes as you like with at most one colour and one background: `bold_highlight_blue`,
`italic_red`, `underline_green`.

- An unknown name, two colours or two backgrounds raise a `ValueError` that names the problem.
- `formatter` takes any object and writes its `str`.
- Each spec is worked out once and remembered.

### Your own colours

`create_colour` adds an RGB colour under a name of your choice, and returns that name. From then on it goes in a
spec as any colour does, alone or as `highlight_<name>`:

```python
from clitint import create_colour, formatter

steel = create_colour("steel", 70, 130, 180)
print(formatter("ok", f"bold_{steel}"), formatter("ok", f"white_highlight_{steel}"))
```

A name is one word without `_`, not already a style; each component is an int from 0 to 255.

`create_multiple_colours` makes several at once and returns their names in order. It is all or nothing: if one
is refused, none are added.

```python
from clitint import create_multiple_colours

steel, sand = create_multiple_colours({"steel": (70, 130, 180), "sand": (194, 178, 128)})
```

> [!WARNING]
> `orange` and the colours after it in the table, and every colour made with `create_colour`, are 24-bit
> sequences. Most terminals of today show them (Windows Terminal, the Windows 10 and 11 console, iTerm2, GNOME
> Terminal, VS Code, tmux 3); an older one shows the text in its default colour. clitint doesn't check what the
> terminal can do: `black` to `grey` work everywhere.

## 🖥️ When text is coloured

`formatter` decides at every call, in this order:

| # | Condition                                                          | Result    |
|---|--------------------------------------------------------------------|-----------|
| 1 | `turn_colours_off()` / `turn_colours_on()` was called              | as chosen |
| 2 | `NO_COLOR`, `ANSI_COLORS_DISABLED` or `CLITINT_COLOURS_OFF=1`      | plain     |
| 3 | `FORCE_COLOR`                                                      | coloured  |
| 4 | `TERM=dumb`                                                        | plain     |
| 5 | otherwise                                                          | coloured only when **both** stdout and stderr are terminals |

`let_the_environment_decide()` undoes rule 1, and `colours_on()` tells you the answer now.

`NO_COLOR` and `FORCE_COLOR` count when they are set to anything but an empty string, as
[no-color.org](https://no-color.org) and [force-color.org](https://force-color.org) say (`FORCE_COLOR=0` forces too).
On Windows 10 and 11 the console is asked to read escape sequences; where it can't, text is plain unless forced.

> [!TIP]
> **Why both streams?** A string doesn't know where it is going: an error message might be printed, logged or
> raised. With `2> errors.log` and stdout on a terminal you still get a plain message, so no escape codes end up in
> the log.

## 🧰 Other tools

### Switching colours from the program

```python
from clitint import turn_colours_off, turn_colours_on, let_the_environment_decide, colours_on

turn_colours_off()              # plain from now on, whatever the environment says (a --no-color flag)
turn_colours_on()               # coloured from now on, even into a file or a pipe (a --color flag)
let_the_environment_decide()    # back to the rules above
colours_on()                    # the answer right now: True or False
```

### Building one message: decide once

Every `formatter` call checks the environment and the streams. That is the only performance bottleneck this library has. It is insignificant for most use cases. However, when a message is built from many pieces (hunderds or thousands of calls to formatter), that can slowdown the process noticeably. Using `one_decision` avoids repeated checks and improves performance in such cases many times over.

```python
from clitint import formatter, one_decision

with one_decision():
    line = formatter("a", "red") + " " + formatter("b", "blue") + " " + formatter("c", "green") + ...
```

Blocks can be nested, and an inner one keeps the outer answer. Something that changes the answer inside the
block, such as `turn_colours_off()`, takes effect only after the block ends. The answer lives in a module global,
so don't build messages in several threads at once.

`decide()`, `decision()` and `release()` do the same without a `with` block, for a library that wraps its own
message building:

```python
from clitint import decide, decision, release

decide()        # check now and keep the answer (returns it)
decision()      # the answer kept, or None if nothing is decided
release()       # forget it: each formatter call checks again
```

### Raw escape sequences, for hot loops

`escapes` gives the sequences that go before and after the text, two per spec, in one flat tuple. They are the
same whether colours are on or not, so check `coloured()` yourself. It returns the answer kept by
`one_decision` / `decide` if there is one, and `colours_on()` otherwise:

```python
from clitint import escapes, coloured

red, reset, bold, bold_reset = escapes("red", "bold")
text = f"{red}x{reset}" if coloured() else "x"
```

`ATTRIBUTES`, `COLOURS` and `BACKGROUNDS` are the tables of names and their sequences, and `ESC` is the reset
sequence (`"\x1b[0m"`).

### Removing colours

```python
from clitint import strip_colours

strip_colours(formatter("x", "red"))   # 'x': every ANSI style sequence removed (for tests and logs)
```

### For a library built on clitint

Give your users an off switch of their own, next to `CLITINT_COLOURS_OFF`:

```python
from clitint import add_off_switch

add_off_switch("MYLIB_COLOURS_OFF")    # MYLIB_COLOURS_OFF=1 now turns colours off too
```

Only the value `1` counts, and it is checked together with the other off switches, before `FORCE_COLOR`.

## 📄 Licence

MIT
