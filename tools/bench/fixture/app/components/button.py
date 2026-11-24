"""The shared button component: every page renders its buttons through it."""
from html import escape

BASE_CLASS = "btn"


def button(label: str, kind: str = "primary", style: str = "") -> str:
    """A button as HTML: the base class, the kind's class and an optional inline style."""
    classes = f"{BASE_CLASS} {BASE_CLASS}-{kind}"
    attr = f' style="{escape(style)}"' if style else ""
    return f'<button class="{classes}"{attr}>{escape(label)}</button>'
