SKILL_TEMPLATE = """---
name: {name}
---

# TODO: tytuł
"""


def scaffold(name):
    return SKILL_TEMPLATE.format(name=name)
