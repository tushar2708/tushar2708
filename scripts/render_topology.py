#!/usr/bin/env python3
"""Render the light and dark graph-ledger assets for the profile README."""

from __future__ import annotations

import argparse
import html
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Theme:
    name: str
    text: str
    muted: str
    surface: str
    border: str
    edge: str
    grid: str
    memory: str
    runtime: str
    tooling: str


THEMES = (
    Theme(
        name="light",
        text="#1f2328",
        muted="#59636e",
        surface="#ffffff",
        border="#d0d7de",
        edge="#8c959f",
        grid="#d8dee4",
        memory="#087f8c",
        runtime="#9a6700",
        tooling="#8250df",
    ),
    Theme(
        name="dark",
        text="#f0f6fc",
        muted="#8b949e",
        surface="#0d1117",
        border="#30363d",
        edge="#6e7681",
        grid="#30363d",
        memory="#56d4dd",
        runtime="#e3b341",
        tooling="#bc8cff",
    ),
)


def _text(
    value: str,
    x: int,
    y: int,
    *,
    size: int,
    fill: str,
    weight: int = 400,
    anchor: str = "start",
    family: str = "sans",
) -> str:
    css_class = "mono" if family == "mono" else "sans"
    return (
        f'<text class="{css_class}" x="{x}" y="{y}" fill="{fill}" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">'
        f'{html.escape(value)}</text>'
    )


def _relation(value: str, x: int, y: int, width: int, theme: Theme) -> str:
    return "\n".join(
        (
            f'<rect x="{x}" y="{y}" width="{width}" height="22" rx="11" '
            f'fill="{theme.surface}" stroke="{theme.border}"/>',
            _text(
                value,
                x + width // 2,
                y + 15,
                size=11,
                fill=theme.muted,
                weight=600,
                anchor="middle",
                family="mono",
            ),
        )
    )


def _workspace(
    *,
    x: int,
    y: int,
    title: str,
    owner: str,
    accent: str,
    theme: Theme,
) -> str:
    return "\n".join(
        (
            f'<circle cx="{x}" cy="{y}" r="18" fill="{theme.surface}" '
            f'stroke="{accent}" stroke-width="3"/>',
            f'<circle cx="{x}" cy="{y}" r="5" fill="{accent}"/>',
            _text(title, x + 32, y - 2, size=20, fill=theme.text, weight=700),
            _text(owner, x + 32, y + 17, size=12, fill=theme.muted, family="mono"),
        )
    )


def _repository(
    *,
    x: int,
    y: int,
    label: str,
    label_y: int,
    accent: str,
    theme: Theme,
) -> str:
    return "\n".join(
        (
            f'<circle cx="{x}" cy="{y}" r="8" fill="{theme.surface}" '
            f'stroke="{accent}" stroke-width="3"/>',
            f'<circle cx="{x}" cy="{y}" r="3" fill="{accent}"/>',
            _text(label, x, label_y, size=14, fill=theme.text, weight=650, anchor="middle"),
        )
    )


def render_svg(theme: Theme) -> str:
    arrow = f"arrow-{theme.name}"
    grid = f"grid-{theme.name}"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="360" '
        'viewBox="0 0 960 360" role="img" aria-labelledby="title desc">',
        '<title id="title">Tushar Dwivedi public work graph</title>',
        '<desc id="desc">A compact graph ledger connecting Tushar Dwivedi to '
        'AI memory, runtime systems, developer tooling, and six public repositories.</desc>',
        '<style>',
        '.sans { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }',
        '.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }',
        '</style>',
        '<defs>',
        f'<pattern id="{grid}" width="24" height="24" patternUnits="userSpaceOnUse">',
        f'<circle cx="1" cy="1" r="0.8" fill="{theme.grid}"/>',
        '</pattern>',
        f'<marker id="{arrow}" viewBox="0 0 10 10" refX="8" refY="5" '
        'markerWidth="5" markerHeight="5" orient="auto-start-reverse">',
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{theme.edge}"/>',
        '</marker>',
        '</defs>',
        f'<rect width="960" height="360" fill="url(#{grid})" opacity="0.55"/>',
        _text("work graph", 24, 28, size=12, fill=theme.muted, family="mono"),
        _text("public systems / current map", 936, 28, size=12, fill=theme.muted, anchor="end", family="mono"),
        # Identity node and its three semantic relationships.
        f'<circle cx="122" cy="180" r="46" fill="{theme.surface}" '
        f'stroke="{theme.text}" stroke-width="2.5"/>',
        f'<circle cx="122" cy="180" r="6" fill="{theme.text}"/>',
        _text("Tushar Dwivedi", 122, 247, size=20, fill=theme.text, weight=750, anchor="middle"),
        _text("builder node", 122, 267, size=12, fill=theme.muted, anchor="middle", family="mono"),
        f'<path d="M 168 180 C 214 180 224 78 286 78" fill="none" stroke="{theme.edge}" '
        f'stroke-width="2" marker-end="url(#{arrow})"/>',
        f'<path d="M 168 180 C 214 180 224 180 286 180" fill="none" stroke="{theme.edge}" '
        f'stroke-width="2" marker-end="url(#{arrow})"/>',
        f'<path d="M 168 180 C 214 180 224 282 286 282" fill="none" stroke="{theme.edge}" '
        f'stroke-width="2" marker-end="url(#{arrow})"/>',
        _relation("building", 190, 96, 70, theme),
        _relation("builds", 194, 168, 60, theme),
        _relation("maintains", 184, 242, 80, theme),
        # Open rails: the project names stay on the graph, while details live in Markdown.
        f'<path d="M 326 78 H 928" stroke="{theme.memory}" stroke-width="1.8" fill="none"/>',
        f'<path d="M 326 180 H 928" stroke="{theme.runtime}" stroke-width="1.8" fill="none"/>',
        f'<path d="M 326 282 H 928" stroke="{theme.tooling}" stroke-width="1.8" fill="none"/>',
        _workspace(x=304, y=78, title="AI memory", owner="SmrutAI", accent=theme.memory, theme=theme),
        _workspace(x=304, y=180, title="runtime systems", owner="Bytonomics", accent=theme.runtime, theme=theme),
        _workspace(x=304, y=282, title="developer tooling", owner="open source", accent=theme.tooling, theme=theme),
        _repository(x=570, y=78, label="smritea-sdk", label_y=56, accent=theme.memory, theme=theme),
        _repository(x=714, y=78, label="pedantigo", label_y=105, accent=theme.memory, theme=theme),
        _repository(x=850, y=78, label="databridge", label_y=56, accent=theme.memory, theme=theme),
        _repository(x=650, y=180, label="smartcache", label_y=158, accent=theme.runtime, theme=theme),
        _repository(x=830, y=180, label="cld-gateway", label_y=207, accent=theme.runtime, theme=theme),
        _repository(x=760, y=282, label="claude-assets", label_y=260, accent=theme.tooling, theme=theme),
        f'<circle cx="928" cy="78" r="3" fill="{theme.memory}"/>',
        f'<circle cx="928" cy="180" r="3" fill="{theme.runtime}"/>',
        f'<circle cx="928" cy="282" r="3" fill="{theme.tooling}"/>',
        # Compact legend doubles as a visual baseline.
        f'<line x1="24" y1="332" x2="936" y2="332" stroke="{theme.border}"/>',
        f'<circle cx="31" cy="347" r="5" fill="{theme.surface}" stroke="{theme.text}" stroke-width="2"/>',
        _text("workspace", 44, 351, size=11, fill=theme.muted, family="mono"),
        f'<circle cx="132" cy="347" r="4" fill="{theme.text}"/>',
        _text("repository", 144, 351, size=11, fill=theme.muted, family="mono"),
        _text("relationships are semantic, not decorative", 936, 351, size=11, fill=theme.muted, anchor="end", family="mono"),
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "assets")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when checked-in assets do not match generated output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []

    for theme in THEMES:
        path = args.output_dir / f"topology-{theme.name}.svg"
        rendered = render_svg(theme)
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != rendered:
                stale.append(str(path))
            continue
        path.write_text(rendered, encoding="utf-8")

    if stale:
        print("Topology assets are stale: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
