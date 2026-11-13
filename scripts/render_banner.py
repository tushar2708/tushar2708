#!/usr/bin/env python3
"""Render original light and dark portrait banners for the profile README."""

from __future__ import annotations

import argparse
import base64
import html
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORTRAIT = ROOT / "assets" / "tushar-banner.jpg"


@dataclass(frozen=True)
class BannerTheme:
    name: str
    base: str
    panel: str
    text: str
    muted: str
    border: str
    grid: str
    accent: str


THEMES = (
    BannerTheme("light", "#edf2f4", "#f8fafb", "#202b38", "#5d6b78", "#c9d3db", "#d7e0e5", "#4f7a89"),
    BannerTheme("dark", "#101923", "#16222d", "#edf3f7", "#aab8c2", "#304353", "#273947", "#81aab8"),
)


def _text(value: str, x: int, y: int, *, size: int, fill: str, weight: int = 400) -> str:
    return f'<text class="sans" x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}">{html.escape(value)}</text>'


def render_svg(theme: BannerTheme) -> str:
    clip, grid = f"portrait-{theme.name}", f"banner-grid-{theme.name}"
    portrait_data = base64.b64encode(PORTRAIT.read_bytes()).decode("ascii")
    return "\n".join((
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="270" viewBox="0 0 960 270" role="img" aria-labelledby="title desc">',
        '<title id="title">Tushar Dwivedi</title>',
        '<desc id="desc">Portrait banner for Tushar Dwivedi, founder and hands-on staff engineer.</desc>',
        '<style>.sans { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }</style>',
        '<defs>',
        f'<pattern id="{grid}" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M 28 0 L 0 0 0 28" fill="none" stroke="{theme.grid}" stroke-width="1"/></pattern>',
        f'<clipPath id="{clip}"><circle cx="162" cy="135" r="86"/></clipPath>',
        '</defs>',
        f'<rect width="960" height="270" rx="16" fill="{theme.base}"/>',
        f'<rect width="960" height="270" rx="16" fill="url(#{grid})" opacity="0.78"/>',
        f'<rect x="25" y="25" width="910" height="220" rx="12" fill="none" stroke="{theme.border}"/>',
        f'<circle cx="162" cy="135" r="96" fill="{theme.panel}" stroke="{theme.accent}" stroke-width="3"/>',
        f'<image href="data:image/jpeg;base64,{portrait_data}" x="76" y="45" width="172" height="197" preserveAspectRatio="xMidYMid slice" clip-path="url(#{clip})"/>',
        f'<circle cx="162" cy="135" r="86" fill="none" stroke="{theme.border}" stroke-width="5" opacity="0.72"/>',
        _text("Hi, I’m Tushar.", 290, 94, size=38, fill=theme.text, weight=760),
        _text("Founder and hands-on staff engineer building AI memory,", 290, 132, size=18, fill=theme.text, weight=530),
        _text("distributed systems, and developer tools—from whiteboard to production scale.", 290, 159, size=18, fill=theme.text, weight=530),
        f'<line x1="290" y1="183" x2="885" y2="183" stroke="{theme.border}"/>',
        f'<circle cx="298" cy="211" r="5" fill="{theme.accent}"/>', _text("Bengaluru", 313, 216, size=13, fill=theme.muted, weight=650),
        f'<circle cx="410" cy="211" r="5" fill="{theme.accent}"/>', _text("Founder at Smritea", 425, 216, size=13, fill=theme.muted, weight=650),
        _text("tushardwivedi.com", 745, 216, size=12, fill=theme.muted, weight=600),
        '</svg>', '',
    ))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "assets")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    for theme in THEMES:
        path = args.output_dir / f"banner-{theme.name}.svg"
        rendered = render_svg(theme)
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != rendered:
                stale.append(str(path))
        else:
            path.write_text(rendered, encoding="utf-8")
    if stale:
        print("Banner assets are stale: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
