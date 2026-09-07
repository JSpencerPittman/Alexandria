# Deployment

`python -m alexandria build` produces `output/` as a directory of plain
HTML, CSS, JS, an RSS feed, and a JSON search index — no server-side code
runs at request time. This project deploys to **GitHub Pages with a
custom domain**, via the workflow already checked in at
`.github/workflows/pages.yml`.

## One-time setup

1. **Set `base_url` in `site.yaml`** to your real domain, e.g.
   `https://yourdomain.com`. This is used for the RSS feed's absolute
   links, and the build also derives the Pages `CNAME` file from it
   automatically (see "How the custom domain stays configured" below) —
   so this one value is the single source of truth, don't set the domain
   anywhere else.
2. **Push this repo to GitHub** (if it isn't already there).
3. **Enable Pages**: repo Settings → Pages → under "Build and
   deployment", set Source to **GitHub Actions**. (Not "Deploy from a
   branch" — the workflow here pushes a build artifact directly, there's
   no `gh-pages` branch involved.)
4. **Point DNS at GitHub Pages**, at your DNS provider:
   - Apex/root domain (`yourdomain.com`): four `A` records to
     `185.199.108.153`, `185.199.109.153`, `185.199.110.153`,
     `185.199.111.153` (and `AAAA` records to GitHub's IPv6 addresses if
     you want IPv6 — see [GitHub's docs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)
     for the current list).
   - Subdomain (`blog.yourdomain.com`): a `CNAME` record pointing at
     `<username>.github.io`.
5. **Set the custom domain in GitHub**: repo Settings → Pages → "Custom
   domain" → enter the same domain as `base_url` (minus the scheme) →
   Save. Once DNS propagates, tick "Enforce HTTPS".
6. Push to `main`. The workflow builds and deploys; check the Actions tab
   for progress, and the Pages settings page for the live URL.

## How the custom domain stays configured

GitHub Pages normally stores the custom domain as a `CNAME` file
alongside your published content. When deploying via a branch, GitHub
writes that file for you; when deploying via a custom Actions workflow
(as here), **it doesn't** — and if a deploy's artifact doesn't contain a
`CNAME` file, GitHub Pages resets/clears the custom domain setting on
that deploy.

To avoid that turning into a recurring surprise, `alexandria/build.py`
writes `output/CNAME` itself, derived from `base_url` in `site.yaml`, on
every build. As long as `base_url` is correct, the custom domain
survives every deploy without you having to think about it again.

## Every subsequent push

Nothing manual — push to `main`, `.github/workflows/pages.yml` builds
with `pip install -e .` + `python -m alexandria build` and publishes
`output/` via `actions/upload-pages-artifact` /
`actions/deploy-pages`. You can also trigger it by hand from the Actions
tab (`workflow_dispatch` is enabled).

## Alternative: self-hosted VPS with Caddy

If you ever want to move off Pages and run your own server instead, the
`output/` directory is still just static files — a VPS running
[Caddy](https://caddyserver.com/) needs only:

```
yourdomain.com {
    root * /var/www/alexandria
    encode gzip
    file_server
}
```

with `output/`'s contents synced to `/var/www/alexandria` (e.g. via
`rsync` from CI, or by building on the server after a `git pull`). Caddy
handles the TLS certificate automatically. This isn't wired up as a
workflow here since Pages is the current target, but nothing about the
generator would need to change to switch.

## Neither option needs

- A database (there isn't one — pages are files).
- A running Python process in production (the generator only runs at
  build time; nothing imports `alexandria` at request time).
