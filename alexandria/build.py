"""Orchestrates a full site build: discover -> render -> write.

Run via `python -m alexandria build`. The whole thing is one pass over
memory (a few hundred markdown files is nothing), so there's no caching or
incremental-build machinery -- if that ever becomes necessary, this is the
one file you'd need to change.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from urllib.parse import urlparse

import markdown as md_lib
from jinja2 import Environment, FileSystemLoader

from .config import SiteConfig
from .feed import render_feed
from .linking import BuildContext, InternalLinkExtension, LinkGraph
from .page import Page, slugify

MARKDOWN_EXTENSIONS = [
    "extra",  # tables, fenced code, footnotes-lite, attr_list, etc.
    "footnotes",
    "toc",
    "codehilite",
    "sane_lists",
    "smarty",
]
MARKDOWN_EXTENSION_CONFIGS = {
    "codehilite": {"guess_lang": False},
    "toc": {"permalink": False},
}


def discover_pages(content_dir: Path) -> list[Page]:
    pages = []
    for path in sorted(content_dir.rglob("*.md")):
        pages.append(Page.from_file(path, content_dir))
    return pages


def assign_urls(pages: list[Page]) -> None:
    for page in pages:
        page.url = "/" if page.slug == "" else f"/{page.slug}/"


def build_key_index(pages: list[Page]) -> dict[str, Page]:
    index: dict[str, Page] = {}
    for page in pages:
        for key in page.wikilink_keys:
            index.setdefault(key, page)
        index.setdefault(slugify(page.slug), page)
    return index


def render_bodies(pages: list[Page], content_dir: Path) -> LinkGraph:
    graph = LinkGraph()
    key_index = build_key_index(pages)
    ctx = BuildContext(key_index, content_dir)
    md = md_lib.Markdown(
        extensions=[*MARKDOWN_EXTENSIONS, InternalLinkExtension(ctx, graph)],
        extension_configs=MARKDOWN_EXTENSION_CONFIGS,
    )
    for page in pages:
        ctx.current = page
        page.body_html = md.convert(page.raw_markdown)
        md.reset()
    return graph


def build(
    config_path: Path = Path("site.yaml"),
    include_drafts: bool = False,
) -> None:
    config = SiteConfig.load(config_path)
    all_pages = discover_pages(config.content_dir)
    pages = [p for p in all_pages if include_drafts or not p.draft]
    assign_urls(pages)
    graph = render_bodies(pages, config.content_dir)

    pages_by_slug = {p.slug: p for p in pages}
    tags: dict[str, list[Page]] = {}
    for page in pages:
        for tag in page.tags:
            tags.setdefault(tag, []).append(page)

    env = Environment(
        loader=FileSystemLoader(str(config.templates_dir)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["site"] = config
    env.globals["all_tags"] = sorted(tags)
    env.filters["slugify"] = slugify

    if config.output_dir.exists():
        shutil.rmtree(config.output_dir)
    config.output_dir.mkdir(parents=True)

    page_template = env.get_template("page.html")
    for page in pages:
        backlinks = sorted(
            (pages_by_slug[s] for s in graph.links_to(page.slug) if s in pages_by_slug),
            key=lambda p: p.title,
        )
        html = page_template.render(page=page, backlinks=backlinks)
        _write(config.output_dir, page.url, html)

    listing_template = env.get_template("listing.html")
    by_date = sorted((p for p in pages if p.date), key=lambda p: p.date, reverse=True)
    _write(
        config.output_dir,
        "/all/",
        listing_template.render(title="All Pages", pages=by_date or pages),
    )

    tag_template = env.get_template("listing.html")
    for tag, tag_pages in tags.items():
        tag_pages_sorted = sorted(tag_pages, key=lambda p: p.date or p.title, reverse=True)
        _write(
            config.output_dir,
            f"/tags/{slugify(tag)}/",
            tag_template.render(title=f"Tag: {tag}", pages=tag_pages_sorted),
        )
    tags_index_template = env.get_template("tags.html")
    _write(
        config.output_dir,
        "/tags/",
        tags_index_template.render(tags={t: len(ps) for t, ps in tags.items()}),
    )

    search_template = env.get_template("search.html")
    _write(config.output_dir, "/search/", search_template.render())

    if config.static_dir.exists():
        shutil.copytree(config.static_dir, config.output_dir / "static")

    (config.output_dir / "feed.xml").write_text(render_feed(pages, config), encoding="utf-8")

    search_index = [
        {"title": p.title, "url": p.url, "summary": p.summary, "tags": p.tags}
        for p in pages
    ]
    (config.output_dir / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False), encoding="utf-8"
    )

    # GitHub Pages resets a custom domain on every Actions-based deploy
    # unless the published output includes a CNAME file, so derive one
    # from base_url rather than making it a separate, easily-stale setting.
    domain = urlparse(config.base_url).netloc
    if domain and domain != "localhost":
        (config.output_dir / "CNAME").write_text(domain + "\n", encoding="utf-8")

    print(f"built {len(pages)} pages -> {config.output_dir}")


def _write(output_dir: Path, url: str, html: str) -> None:
    if url == "/":
        target = output_dir / "index.html"
    else:
        target = output_dir / url.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
