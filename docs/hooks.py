"""
MkDocs hooks (mkdocs.yml, ``hooks``): the home page is README.md, read as GitHub reads it.
"""
from pathlib import Path
from typing import Any
import re

README = Path(__file__).resolve().parent.parent / "README.md"

#* A GitHub alert: `> [!NOTE]` and the quoted lines below it.
_ALERT = re.compile(r"^> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\n((?:>.*\n?)*)", re.MULTILINE)
_ADMONITION = {"NOTE": "note", "TIP": "tip", "IMPORTANT": "info", "WARNING": "warning", "CAUTION": "danger"}


def _admonition(match: re.Match[str]) -> str:
    """A GitHub alert as the admonition MkDocs shows the same way (`!!! tip`, its text indented)."""
    lines = [line[2:] if line.startswith("> ") else line[1:] for line in match.group(2).splitlines()]
    return f"!!! {_ADMONITION[match.group(1)]}\n\n" + "".join(f"    {line}\n" for line in lines) + "\n"


def on_page_markdown(markdown: str, page: Any, **_: Any) -> str:
    if page.file.src_uri != "index.md":
        return markdown
    #* The README itself, read here rather than through an include: an include is expanded after
    #* this hook, too late for the changes below. GitHub reads Markdown inside the README's centred
    #* header; Python-Markdown does only where the block says so (md_in_html), so the attribute is
    #* added here and the README stays as GitHub wants it. GitHub's alerts (`> [!TIP]`) are a
    #* quote to Python-Markdown, so they are turned into the admonitions that look the same.
    text = README.read_text(encoding = "utf-8").replace('<div align="center">', '<div align="center" markdown>')
    return _ALERT.sub(_admonition, text)
