"""Minimal RSS 2.0 feed generation -- hand-rolled to avoid a feed-writing
dependency; RSS is a small enough format that string templating is fine."""
from __future__ import annotations

import datetime as dt
from email.utils import format_datetime
from xml.sax.saxutils import escape

from .config import SiteConfig
from .page import Page

RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{title}</title>
  <link>{link}</link>
  <description>{description}</description>
  <lastBuildDate>{build_date}</lastBuildDate>
{items}</channel>
</rss>
"""

ITEM_TEMPLATE = """  <item>
    <title>{title}</title>
    <link>{link}</link>
    <guid>{link}</guid>
    <description>{description}</description>
    <pubDate>{pub_date}</pubDate>
  </item>
"""


def render_feed(pages: list[Page], config: SiteConfig) -> str:
    dated = [p for p in pages if p.date is not None]
    dated.sort(key=lambda p: p.date, reverse=True)
    items = []
    for page in dated[: config.feed_length]:
        link = config.base_url.rstrip("/") + page.url
        pub_date = format_datetime(dt.datetime.combine(page.date, dt.time()))
        items.append(
            ITEM_TEMPLATE.format(
                title=escape(page.title),
                link=escape(link),
                description=escape(page.summary),
                pub_date=pub_date,
            )
        )
    return RSS_TEMPLATE.format(
        title=escape(config.title),
        link=escape(config.base_url),
        description=escape(config.description),
        build_date=format_datetime(dt.datetime.now()),
        items="".join(items),
    )
