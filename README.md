# clitint

Coloured terminal text for Python 3.13+, with no dependencies. Text is coloured only when someone is reading it
on a terminal: redirect the output to a file, a pipe or a CI log and it comes out plain.

```python
from clitint import formatter

print(formatter("error:", "bold_red"), "file not found")
print(formatter("warning", "underline_black_highlight_yellow"))
```

## Install

```bash
pip install clitint
```

## Specs

A spec is a set of styles joined by `_`, in any order: `"red"`, `"bold_red"`, `"red_bold"`, `"italic_white_highlight_blue"`.

| Kind | Names |
|---|---|
| Attributes | `bold`, `dim`, `italic`, `underline` |
| Colours | `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`, `grey`, `orange` |
| Backgrounds | `highlight_` followed by a colour: `highlight_blue` |


You can also combine: bold_highlight_blue, italic_red, underline_green, etc.

An unknown name, two colours or two backgrounds raise a `ValueError` that names the problem. `formatter` takes any
object and writes its `str`. Each spec is worked out once and remembered.

## When text is coloured

`formatter` decides at every call, in this order:

1. what the program chose: `turn_colours_off()` or `turn_colours_on()` (`let_the_environment_decide()` undoes it);
2. `CLITINT_COLOURS_OFF=1`, `NO_COLOR` or `ANSI_COLORS_DISABLED`: plain;
3. `FORCE_COLOR`: coloured;
4. `TERM=dumb`: plain;
5. otherwise, coloured only when **both** stdout and stderr are terminals.

The last rule is there because a string doesn't know where it is going. An error message might be printed,
logged or raised. `2> errors.log` with stdout on a terminal still gives a plain message, so no escape codes end up
in the log.

`colours_on()` tells you the answer now.

## Other tools

```python
from clitint import strip_colours, escapes, one_decision, coloured

strip_colours(formatter("x", "red"))        # 'x': every ANSI style sequence removed (for tests and logs)

with one_decision():                        # one message: decide once, not at every formatter call
    line = formatter("a", "red") + " " + formatter("b", "blue")

red, reset = escapes("red")                 # the raw sequences, for a hot f-string
text = f"{red}x{reset}" if coloured() else "x"
```

## Licence

MIT
