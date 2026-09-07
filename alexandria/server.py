"""Local development server: serves output/ and, with --watch, rebuilds
whenever a source file changes. Deliberately just stdlib (http.server +
mtime polling) so there's no extra dependency for something this small."""
from __future__ import annotations

import functools
import http.server
import threading
import time
from pathlib import Path

from .build import build
from .config import SiteConfig


def _mtimes(paths: list[Path]) -> dict[Path, float]:
    stamps: dict[Path, float] = {}
    for base in paths:
        if not base.exists():
            continue
        if base.is_file():
            stamps[base] = base.stat().st_mtime
        else:
            for f in base.rglob("*"):
                if f.is_file():
                    stamps[f] = f.stat().st_mtime
    return stamps


def _watch(config: SiteConfig, config_path: Path, interval: float = 1.0) -> None:
    watched = [config.content_dir, config.templates_dir, config.static_dir, config_path]
    last = _mtimes(watched)
    while True:
        time.sleep(interval)
        current = _mtimes(watched)
        if current != last:
            last = current
            print("change detected, rebuilding...")
            try:
                build(config_path)
            except Exception as exc:  # keep the server alive on a bad edit
                print(f"build failed: {exc}")


def serve(config_path: Path = Path("site.yaml"), port: int = 8000, watch: bool = True) -> None:
    config = SiteConfig.load(config_path)
    build(config_path)

    if watch:
        threading.Thread(target=_watch, args=(config, config_path), daemon=True).start()

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(config.output_dir))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"serving {config.output_dir} at http://127.0.0.1:{port}/ (watch={watch})")
        httpd.serve_forever()
