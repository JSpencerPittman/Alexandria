---
title: Hello, World
date: 2026-01-05
tags: [meta]
summary: The first post -- a short tour of the site's markup conventions.
---

This is the first real post, mostly here to demonstrate the markup this
generator understands.

A footnote looks like this.[^1] Fenced code blocks get syntax highlighting
via Pygments:

```python
def slugify(text: str) -> str:
    return text.strip().lower().replace(" ", "-")
```

You can reference another page two ways. A wikilink, resolved by title or
slug: see [[On Note-Taking]] for the follow-up post. Or an ordinary
markdown link straight to the source file, which gets rewritten to the
right URL at build time: [the same post](../essays/on-note-taking.md).

Either way the link becomes hoverable, and the target page will list this
one under "Linked from" automatically.

[^1]: Footnotes use python-markdown's `footnotes` extension -- nothing
    custom here.
