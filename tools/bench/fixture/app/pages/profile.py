"""The Profile page."""
from html import escape

from app.components.button import button


def render(items: list[str]) -> str:
    rows = "".join(f"<li>{escape(name)}</li>" for name in items)
    return f"<h1>Profile</h1><ul>{rows}</ul>" + button("Discard", kind="secondary", style="width: 100%")
