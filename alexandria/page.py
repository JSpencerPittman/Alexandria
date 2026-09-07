"""Parsing of a single content/*.md file into a Page object.

A Page is deliberately a plain dataclass with no behaviour beyond parsing
itself from disk -- rendering, link resolution, and backlink tracking all
happen in build.py / linking.py so it's obvious where to look when you want
to change something.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)
HEADING_RE = re.compile(r"^\s*#\s+(.+)$", re.MULTILINE)
MD_STRIP_RE = re.compile(r"[#*_`>\[\]]|\[\[|\]\]")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9/\-\s]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def plain_excerpt(markdown_text: str, length: int = 280) -> str:
    """A rough, good-enough-for-a-tooltip plaintext excerpt of raw markdown."""
    text = markdown_text.strip()
    text = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)  # stray frontmatter
    # take the first non-empty paragraph
    for para in text.split("\n\n"):
        para = para.strip()
        if para and not para.startswith("#"):
            break
    else:
        para = text
    para = LINK_RE.sub(r"\1", para)
    para = MD_STRIP_RE.sub("", para)
    para = re.sub(r"\s+", " ", para).strip()
    if len(para) > length:
        para = para[:length].rsplit(" ", 1)[0] + "…"
    return para


@dataclass
class Page:
    path: Path
    slug: str
    title: str
    raw_markdown: str
    date: dt.date | None = None
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    summary: str = ""
    draft: bool = False
    meta: dict = field(default_factory=dict)

    # populated during the build, not at parse time
    body_html: str = ""
    url: str = ""

    @classmethod
    def from_file(cls, path: Path, content_dir: Path) -> "Page":
        raw = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(raw)
        if match:
            frontmatter = yaml.safe_load(match.group(1)) or {}
            body = match.group(2)
        else:
            frontmatter = {}
            body = raw

        rel = path.relative_to(content_dir).with_suffix("")
        default_slug = "" if rel.name == "index" and rel.parent == Path(".") else str(rel).replace("\\", "/")
        slug = str(frontmatter.get("slug", default_slug)).strip("/")

        title = frontmatter.get("title")
        if not title:
            heading = HEADING_RE.search(body)
            title = heading.group(1).strip() if heading else path.stem.replace("-", " ").title()

        date = frontmatter.get("date")
        if isinstance(date, str):
            date = dt.date.fromisoformat(date)

        return cls(
            path=path,
            slug=slug,
            title=title,
            raw_markdown=body,
            date=date,
            tags=list(frontmatter.get("tags", []) or []),
            aliases=list(frontmatter.get("aliases", []) or []),
            summary=frontmatter.get("summary", "") or plain_excerpt(body),
            draft=bool(frontmatter.get("draft", False)),
            meta=frontmatter,
        )

    @property
    def wikilink_keys(self) -> list[str]:
        """Every key by which [[...]] may refer to this page."""
        keys = {slugify(self.slug), slugify(self.title), slugify(Path(self.slug).name)}
        keys.update(slugify(a) for a in self.aliases)
        keys.discard("")
        return list(keys)
