"""Site-wide configuration, loaded from site.yaml."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SiteConfig:
    title: str = "Untitled"
    author: str = ""
    base_url: str = "http://localhost:8000"
    description: str = ""
    nav: list[dict] = field(default_factory=list)
    content_dir: Path = Path("content")
    output_dir: Path = Path("output")
    templates_dir: Path = Path("templates")
    static_dir: Path = Path("static")
    feed_length: int = 20

    @classmethod
    def load(cls, path: Path = Path("site.yaml")) -> "SiteConfig":
        if not path.exists():
            return cls()
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for key in ("content_dir", "output_dir", "templates_dir", "static_dir"):
            if key in data:
                data[key] = Path(data[key])
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
