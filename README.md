# Alexandria

A minimal static site generator for a blog built around dense
cross-linking, in the spirit of [gwern.net](https://gwern.net/about).
You write plain markdown files; the generator resolves `[[wikilinks]]`,
tracks who-links-to-whom automatically ("backlinks", Wikipedia's
"what links here"), and attaches hover-preview popups to internal links —
all as a build step that emits plain HTML you can host anywhere.

There is no database, no server-side rendering at request time, and no
JS framework. The entire runtime dependency list is `Markdown`, `Pygments`
(syntax highlighting), `PyYAML` (frontmatter), and `Jinja2` (templates).

## How it works

1. You write `.md` files under `content/`, with a small YAML frontmatter
   block for title/date/tags.
2. `python -m alexandria build` parses every file, resolves links between
   them, renders each through a Jinja2 template, and writes static HTML
   into `output/`.
3. You deploy `output/` — see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

The two linking mechanisms:

- **Wikilinks**: `[[On Note-Taking]]` or `[[some-slug|custom text]]`.
  Resolved against every page's title, slug, and any `aliases:` in its
  frontmatter. If nothing matches, it renders as a visible "broken link"
  (red, wavy-underlined) rather than failing silently or as plain text —
  so a typo is obvious the moment you build.
- **Relative markdown links**: `[see also](../essays/other-post.md)`.
  Ordinary links that happen to point at another content file are
  rewritten to the right final URL automatically. This means you can
  `Ctrl+click` a link in your editor or on GitHub and it'll actually open
  the right file, unlike a wikilink.

Either kind of link, once resolved, gets `class="internal-link"` and a
`data-preview` attribute holding a plaintext excerpt of the target page.
`static/js/popups.js` reads that attribute to show a hover preview — no
network request, no JS framework, ~60 lines.

Backlinks: while rendering, every resolved internal link is recorded as
an edge in a link graph. After all pages are rendered, each page's
template gets the full list of pages that link to it, shown as
"Linked from" at the bottom.

## Quickstart

```sh
python -m venv .venv
.venv/Scripts/activate       # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -e .

python -m alexandria new "My First Post"   # scaffolds content/essays/my-first-post.md
python -m alexandria build                 # renders content/ -> output/
python -m alexandria serve                 # build + serve http://127.0.0.1:8000, rebuilds on save
```

`alexandria serve` polls `content/`, `templates/`, and `static/` for
changes every second and rebuilds automatically (plain `mtime` polling —
no filesystem-watcher dependency). Use `--no-watch` to disable that, or
`--port` to change the port.

## Writing a page

```markdown
---
title: On Note-Taking
date: 2026-02-14
tags: [meta, writing]
summary: Optional one-liner used for the hover popup and RSS description.
aliases: [notes]     # optional extra names this page can be wikilinked by
draft: false         # true excludes it from `build` unless --drafts is passed
---

Body goes here, referencing [[Hello, World]] or
[a specific file](../essays/hello-world.md).
```

- `title` defaults to the first `# heading` in the body, or the filename.
- `slug` (and therefore URL) defaults to the file's path under `content/`
  without the extension, e.g. `content/essays/foo.md` → `/essays/foo/`.
  Set `slug:` in frontmatter to override.
- `summary` defaults to a naive plaintext excerpt of the first paragraph
  if you don't set one — good enough for a popup, worth writing by hand
  for anything you care about.
- Drafts (`draft: true`) are skipped by `build` unless you pass `--drafts`,
  so you can commit in-progress pieces without publishing them.

Markdown extensions enabled: tables, fenced code blocks with Pygments
syntax highlighting, footnotes, `attr_list`, and smart typography
(straight quotes/dashes become curly quotes/en-dashes).

## Project layout

```
content/            your markdown source — the only directory you write in day-to-day
templates/           Jinja2 templates (base.html, page.html, listing.html, tags.html, search.html)
static/               CSS + the two small JS files (popups, search)
alexandria/            the generator itself
  page.py               parses one .md file into a Page
  linking.py             wikilinks, backlink graph, popup data — the interesting file
  build.py                orchestrates discovery -> render -> write
  feed.py                  RSS
  server.py                 dev server + watch loop
  cli.py                     `python -m alexandria ...`
site.yaml            site title/author/base_url/nav — edit before deploying
output/              generated; gitignored
```

Nothing here is hidden behind abstraction for its own sake — `build.py` is
a single top-to-bottom function you can read in a few minutes, and it's
the first place to look if you want to change how the site is assembled.

## Extending it

Things you might reasonably want to add, none of which require touching
the link graph:

- **Sitemap.xml** for search engines — same shape as `feed.py`.
- **Sidenotes** (margin-positioned footnotes on wide viewports) — CSS +
  a small JS reposition pass; gwern.net's version is the reference.
- **Image thumbnails in popups** — extend `_preview_attrs` in
  `linking.py` to also stash a `data-preview-image`.
