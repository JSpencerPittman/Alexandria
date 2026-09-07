"""The heart of the site: wikilinks, backlinks, and hover-preview data.

Two mechanisms feed the link graph:

1. ``[[Page Title]]`` or ``[[some-slug|display text]]`` -- a wikilink,
   resolved against every page's title/slug/aliases.
2. Plain markdown links that happen to point at another piece of content,
   either by relative path (``[see also](../notes/foo.md)``) or by final
   URL (``[see also](/notes/foo/)``).

Either way, once a link resolves to a known Page we do three things to the
anchor tag: tag it ``class="internal-link"``, attach a ``data-preview``
excerpt (read by static/js/popups.js to render a gwern-style hover popup),
and record the edge in the shared LinkGraph so the target page can list
"linked from" pages -- Wikipedia's "what links here", automatically.
"""
from __future__ import annotations

import xml.etree.ElementTree as etree
from collections import defaultdict
from pathlib import Path

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor

from .page import Page, slugify

WIKILINK_RE = r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"


class LinkGraph:
    """Accumulates edges discovered while rendering every page."""

    def __init__(self) -> None:
        self.backlinks: dict[str, set[str]] = defaultdict(set)

    def add(self, source_slug: str, target_slug: str) -> None:
        # note: the homepage's slug is "" (falsy but valid), so check
        # explicitly for None rather than truthiness.
        if source_slug is not None and target_slug is not None and source_slug != target_slug:
            self.backlinks[target_slug].add(source_slug)

    def links_to(self, slug: str) -> set[str]:
        return self.backlinks.get(slug, set())


class BuildContext:
    """Mutable state the build loop updates between pages.

    A single markdown.Markdown instance is reused for every page (that's
    how footnote/toc numbering etc. stay independent per-page via reset()),
    so the link extension needs to be told which page is "current" before
    each convert() call.
    """

    def __init__(self, pages_by_key: dict[str, Page], content_dir: Path):
        self.pages_by_key = pages_by_key
        self.content_dir = content_dir
        self.current: Page | None = None


def _preview_attrs(target: Page) -> dict[str, str]:
    return {
        "class": "internal-link",
        "data-preview-title": target.title,
        "data-preview": target.summary,
    }


class WikiLinkInlineProcessor(InlineProcessor):
    def __init__(self, pattern: str, ctx: BuildContext, graph: LinkGraph):
        super().__init__(pattern)
        self.ctx = ctx
        self.graph = graph

    def handleMatch(self, m, data):  # noqa: N802 (matching superclass name)
        target_text = m.group(1).strip()
        label = (m.group(2) or target_text).strip()
        target = self.ctx.pages_by_key.get(slugify(target_text))

        if target is None:
            span = etree.Element("span")
            span.set("class", "broken-link")
            span.set("title", "no such page: " + target_text)
            span.text = label
            return span, m.start(0), m.end(0)

        el = etree.Element("a")
        el.set("href", target.url)
        for k, v in _preview_attrs(target).items():
            el.set(k, v)
        el.text = label
        if self.ctx.current is not None:
            self.graph.add(self.ctx.current.slug, target.slug)
        return el, m.start(0), m.end(0)


class InternalLinkTreeprocessor(Treeprocessor):
    """Catches ordinary markdown links that point at other content, e.g.
    ``[see also](../notes/foo.md)`` or ``[see also](/notes/foo/)``."""

    def __init__(self, md, ctx: BuildContext, graph: LinkGraph):
        super().__init__(md)
        self.ctx = ctx
        self.graph = graph

    def run(self, root):
        current = self.ctx.current
        if current is None:
            return
        for a in root.iter("a"):
            href = a.get("href", "")
            if not href or a.get("class") == "internal-link":
                continue  # already a resolved wikilink
            target = self._resolve(href, current)
            if target is None:
                continue
            a.set("href", target.url)
            for k, v in _preview_attrs(target).items():
                a.set(k, v)
            self.graph.add(current.slug, target.slug)

    def _resolve(self, href: str, current: Page) -> Page | None:
        if href.startswith(("http://", "https://", "mailto:", "#")):
            return None
        if href.endswith(".md") or ".md#" in href:
            path = (current.path.parent / href.split("#")[0]).resolve()
            try:
                rel = path.relative_to(self.ctx.content_dir.resolve()).with_suffix("")
            except ValueError:
                return None
            return self.ctx.pages_by_key.get(slugify(str(rel).replace("\\", "/")))
        # a direct site-relative URL, e.g. "/notes/foo/"
        slug = href.strip("/").split("#")[0]
        return self.ctx.pages_by_key.get(slugify(slug))


class InternalLinkExtension(Extension):
    def __init__(self, ctx: BuildContext, graph: LinkGraph):
        self.ctx = ctx
        self.graph = graph
        super().__init__()

    def extendMarkdown(self, md):
        md.inlinePatterns.register(
            WikiLinkInlineProcessor(WIKILINK_RE, self.ctx, self.graph), "wikilink", 175
        )
        md.treeprocessors.register(
            InternalLinkTreeprocessor(md, self.ctx, self.graph), "internal_links", 4
        )
