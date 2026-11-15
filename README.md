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
> For 256 colours, RGB or themes, use another library.

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
| Colours     | `black` `red` `green` `yellow` `blue` `magenta` `cyan` `white` `grey` `orange`           |
| Backgrounds | `highlight_` followed by a colour, e.g. `highlight_blue`                                 |

Combine as many attributes as you like with at most one colour and one background: `bold_highlight_blue`,
`italic_red`, `underline_green`.

- An unknown name, two colours or two backgrounds raise a `ValueError` that names the problem.
- `formatter` takes any object and writes its `str`.
- Each spec is worked out once and remembered.

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

```python
from clitint import strip_colours, escapes, one_decision, coloured

strip_colours(formatter("x", "red"))        # 'x': every ANSI style sequence removed (for tests and logs)

with one_decision():                        # one message: decide once, not at every formatter call
    line = formatter("a", "red") + " " + formatter("b", "blue")

red, reset = escapes("red")                 # the raw sequences, for a hot f-string
text = f"{red}x{reset}" if coloured() else "x"
```

## 📄 Licence

MIT
