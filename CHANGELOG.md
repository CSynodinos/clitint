# Changelog

All notable changes to clitint. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
the project uses [semantic versioning](https://semver.org/) (before 1.0, a minor or patch release may still change
the API; such changes are listed under **Changed** and marked **breaking**).

## [Unreleased]

### Added

- **A documentation site**: [csynodinos.github.io/clitint](https://csynodinos.github.io/clitint/), made from the
  README and this changelog.

## [0.1.6] - 2026-11-16

### Fixed

- The README's picture shows the example as it is now, with a colour made by `create_colour`.

## [0.1.5] - 2026-11-16

### Added

- **Your own colours**: `create_colour(name, red, green, blue)` adds a 24-bit colour under a name and returns the
  name, to use in any spec (`f"bold_{name}"`, `f"highlight_{name}"`). Creating a name again with the same
  components does nothing, so two libraries can each create the colour they need; other components under a name
  already taken raise a `ValueError`.
- `create_multiple_colours({name: (red, green, blue)})`: several at once, all or none.
- **24-bit colour only where it shows.** `orange` and the colours after it, and those of `create_colour`, are
  written where the terminal says it shows 24-bit colour (`COLORTERM=truecolor`, Windows Terminal, iTerm2,
  VS Code, kitty and others) or colours are forced. Elsewhere the text is plain, with one `TrueColourWarning` per
  process.
- `with one_decision() as on:` gives the answer.

### Changed

- **Breaking:** `coloured()` is removed. `colours_on()` now gives the answer kept by `one_decision` or `decide`,
  which is what `coloured()` did.
- **Breaking:** `ATTRIBUTES`, `COLOURS` and `BACKGROUNDS` are read-only views. `create_colour` is the way to add a
  colour.

## [0.1.4] - 2026-11-16

### Added

- Ten more 24-bit colours, as text and as background: `pink`, `purple`, `brown`, `teal`, `gold`, `maroon`,
  `navy`, `olive`, `coral`, `lime`.

### Changed

- **Breaking:** the reset sequence is `ESC` (it was `RESET`).

## [0.1.3] - 2026-11-15

### Changed

- **Faster to import:** nothing but `os` and `sys` is imported (`typing` and `re` were most of a 4 ms start);
  `strip_colours` imports `re` at its first call.
- Faster check of the environment, and a long text is copied once, not twice.

## [0.1.2] - 2026-11-15

### Changed

- `NO_COLOR` and `FORCE_COLOR` count only when they are not empty, as no-color.org and force-color.org say
  (`FORCE_COLOR=0` forces). `NO_COLOR` is now read before `CLITINT_COLOURS_OFF`.

### Added

- **Windows 10 and 11:** the console is asked, once, to read escape sequences. Where it can't, text is plain
  unless colours are forced.

## [0.1.1] - 2026-11-15

No change to the package: a new version number for the upload.

## [0.1.0] - 2026-11-15

The first release. Requires Python 3.13 or later; no dependencies.

### Added

- `formatter(text, spec)`: text in a style given as names joined by `_` (`"bold_red"`,
  `"underline_black_highlight_yellow"`). Attributes `bold`, `dim`, `italic`, `underline`; ten colours; and the
  same as backgrounds (`highlight_<colour>`). An unknown name, two colours or two backgrounds are a `ValueError`.
- Coloured only when both stdout and stderr are terminals, so no escape codes end up in a redirected log.
  `NO_COLOR`, `ANSI_COLORS_DISABLED`, `CLITINT_COLOURS_OFF=1`, `FORCE_COLOR` and `TERM=dumb` are read at every
  call.
- `turn_colours_off()`, `turn_colours_on()`, `let_the_environment_decide()`, `colours_on()`.
- `one_decision()`, and `decide()` / `decision()` / `release()`: one answer for a whole message.
- `add_off_switch(name)`: a library's own off variable.
- `escapes(*specs)` for the raw sequences, and `strip_colours(text)`.

[Unreleased]: https://github.com/CSynodinos/clitint/compare/v0.1.6...HEAD
[0.1.6]: https://github.com/CSynodinos/clitint/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/CSynodinos/clitint/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/CSynodinos/clitint/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/CSynodinos/clitint/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/CSynodinos/clitint/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/CSynodinos/clitint/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/CSynodinos/clitint/releases/tag/v0.1.0
