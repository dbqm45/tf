"""The Settings page."""
from html import escape

from app.components.button import button


def render(items: list[str]) -> str:
    rows = "".join(f"<li>{escape(name)}</li>" for name in items)
    return f"<h1>Settings</h1><ul>{rows}</ul>" + button("Save", kind="primary", style="width: 100%")
