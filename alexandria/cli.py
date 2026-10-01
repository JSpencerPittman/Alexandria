"""Command-line entry point: python -m alexandria <command>."""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from .build import build as run_build
from .config import SiteConfig
from .page import slugify
from .server import serve as run_serve

NEW_PAGE_TEMPLATE = """---
title: {title}
date: {date}
tags: []
draft: true
---

"""


def cmd_build(args: argparse.Namespace) -> None:
    run_build(Path(args.config), include_drafts=args.drafts)


def cmd_serve(args: argparse.Namespace) -> None:
    run_serve(Path(args.config), port=args.port, watch=not args.no_watch)


def cmd_new(args: argparse.Namespace) -> None:
    config = SiteConfig.load(Path(args.config))
    slug = slugify(args.title)
    target = config.content_dir / "essays" / f"{slug}.md" if not args.path else Path(args.path)
    if target.exists():
        raise SystemExit(f"{target} already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        NEW_PAGE_TEMPLATE.format(title=args.title, date=dt.date.today().isoformat()),
        encoding="utf-8",
    )
    print(f"created {target}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="alexandria")
    parser.add_argument("--config", default="site.yaml", help="path to site.yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="build the site into output/")
    p_build.add_argument("--drafts", action="store_true", help="include draft pages")
    p_build.set_defaults(func=cmd_build)

    p_serve = sub.add_parser("serve", help="build and serve output/ locally")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--no-watch", action="store_true", help="disable rebuild-on-change")
    p_serve.set_defaults(func=cmd_serve)

    p_new = sub.add_parser("new", help="scaffold a new content page")
    p_new.add_argument("title", help="page title, e.g. 'On Interlinking'")
    p_new.add_argument("--path", help="explicit path under content/ (default: derived slug)")
    p_new.set_defaults(func=cmd_new)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
