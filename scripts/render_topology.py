#!/usr/bin/env python3
"""Render the light and dark systems-topology assets for the profile README."""

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
    surface_subtle: str
    border: str
    edge: str
    memory: str
    runtime: str
    tooling: str


THEMES = (
    Theme(
        name="light",
        text="#1f2328",
        muted="#59636e",
        surface="#ffffff",
        surface_subtle="#f6f8fa",
        border="#d0d7de",
        edge="#8c959f",
        memory="#087f8c",
        runtime="#9a6700",
        tooling="#8250df",
    ),
    Theme(
        name="dark",
        text="#f0f6fc",
        muted="#8b949e",
        surface="#161b22",
        surface_subtle="#0d1117",
        border="#30363d",
        edge="#6e7681",
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
) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{html.escape(value)}</text>'
    )


def _project_node(
    *,
    x: int,
    y: int,
    title: str,
    description: str,
    accent: str,
    theme: Theme,
) -> str:
    return "\n".join(
        (
            f'<circle cx="{x}" cy="{y}" r="10" fill="{theme.surface}" '
            f'stroke="{accent}" stroke-width="4"/>',
            _text(title, x + 28, y - 2, size=19, fill=theme.text, weight=650),
            _text(description, x + 28, y + 18, size=13, fill=theme.muted),
        )
    )


def _org_node(
    *,
    x: int,
    y: int,
    title: str,
    subtitle: str,
    accent: str,
    theme: Theme,
) -> str:
    return "\n".join(
        (
            f'<rect x="{x}" y="{y}" width="210" height="76" rx="18" '
            f'fill="{theme.surface}" stroke="{accent}" stroke-width="2"/>',
            f'<circle cx="{x + 24}" cy="{y + 25}" r="7" fill="{accent}"/>',
            _text(title, x + 42, y + 31, size=21, fill=theme.text, weight=700),
            _text(subtitle, x + 24, y + 55, size=13, fill=theme.muted),
        )
    )


def _relationship_label(*, value: str, x: int, y: int, width: int, theme: Theme) -> str:
    return "\n".join(
        (
            f'<rect x="{x}" y="{y}" width="{width}" height="22" rx="11" '
            f'fill="{theme.surface}" stroke="{theme.border}" stroke-width="1"/>',
            _text(
                value,
                x + width // 2,
                y + 15,
                size=12,
                fill=theme.muted,
                weight=600,
                anchor="middle",
            ),
        )
    )


def render_svg(theme: Theme) -> str:
    marker_id = f"arrow-{theme.name}"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" '
        'viewBox="0 0 960 540" role="img" aria-labelledby="title desc">',
        '<title id="title">Tushar Dwivedi systems topology</title>',
        '<desc id="desc">A layered map from Tushar Dwivedi through SmrutAI, '
        'Bytonomics, and open source to six public projects.</desc>',
        '<style>text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }</style>',
        '<defs>',
        f'<marker id="{marker_id}" viewBox="0 0 10 10" refX="8" refY="5" '
        'markerWidth="5" markerHeight="5" orient="auto-start-reverse">',
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{theme.edge}"/>',
        '</marker>',
        '</defs>',
        f'<rect x="322" y="20" width="608" height="172" rx="28" fill="{theme.surface_subtle}" '
        f'stroke="{theme.border}" stroke-width="1"/>',
        f'<rect x="322" y="206" width="608" height="150" rx="28" fill="{theme.surface_subtle}" '
        f'stroke="{theme.border}" stroke-width="1"/>',
        f'<rect x="322" y="370" width="608" height="138" rx="28" fill="{theme.surface_subtle}" '
        f'stroke="{theme.border}" stroke-width="1"/>',
        f'<path d="M 256 270 C 294 270, 300 98, 356 98" fill="none" stroke="{theme.edge}" '
        f'stroke-width="2" marker-end="url(#{marker_id})"/>',
        f'<path d="M 256 270 C 300 270, 312 271, 356 271" fill="none" stroke="{theme.edge}" '
        f'stroke-width="2" marker-end="url(#{marker_id})"/>',
        f'<path d="M 256 270 C 294 270, 300 433, 356 433" fill="none" stroke="{theme.edge}" '
        f'stroke-width="2" marker-end="url(#{marker_id})"/>',
        _relationship_label(value="founded", x=264, y=151, width=68, theme=theme),
        _relationship_label(value="builds", x=270, y=244, width=58, theme=theme),
        _relationship_label(value="maintains", x=260, y=348, width=76, theme=theme),
        f'<path d="M 566 98 C 610 98, 610 58, 656 58" fill="none" stroke="{theme.memory}" stroke-width="2"/>',
        f'<path d="M 566 98 C 610 98, 610 111, 656 111" fill="none" stroke="{theme.memory}" stroke-width="2"/>',
        f'<path d="M 566 98 C 610 98, 610 164, 656 164" fill="none" stroke="{theme.memory}" stroke-width="2"/>',
        f'<path d="M 566 271 C 610 271, 610 245, 656 245" fill="none" stroke="{theme.runtime}" stroke-width="2"/>',
        f'<path d="M 566 271 C 610 271, 610 314, 656 314" fill="none" stroke="{theme.runtime}" stroke-width="2"/>',
        f'<path d="M 566 433 C 610 433, 610 439, 656 439" fill="none" stroke="{theme.tooling}" stroke-width="2"/>',
        f'<rect x="30" y="220" width="226" height="100" rx="24" fill="{theme.surface}" '
        f'stroke="{theme.text}" stroke-width="2"/>',
        f'<circle cx="58" cy="249" r="8" fill="{theme.text}"/>',
        _text("Tushar Dwivedi", 78, 256, size=22, fill=theme.text, weight=750),
        _text("founder · staff engineer", 58, 290, size=15, fill=theme.muted),
        _org_node(
            x=356,
            y=60,
            title="SmrutAI",
            subtitle="AI memory infrastructure",
            accent=theme.memory,
            theme=theme,
        ),
        _org_node(
            x=356,
            y=233,
            title="Bytonomics",
            subtitle="systems & developer tools",
            accent=theme.runtime,
            theme=theme,
        ),
        _org_node(
            x=356,
            y=395,
            title="Open source",
            subtitle="personal workbench",
            accent=theme.tooling,
            theme=theme,
        ),
        _project_node(
            x=666,
            y=58,
            title="smritea-sdk",
            description="five-language memory SDK",
            accent=theme.memory,
            theme=theme,
        ),
        _project_node(
            x=666,
            y=111,
            title="pedantigo",
            description="validation & schema",
            accent=theme.memory,
            theme=theme,
        ),
        _project_node(
            x=666,
            y=164,
            title="databridge",
            description="incremental ingestion",
            accent=theme.memory,
            theme=theme,
        ),
        _project_node(
            x=666,
            y=245,
            title="smartcache",
            description="production cache semantics",
            accent=theme.runtime,
            theme=theme,
        ),
        _project_node(
            x=666,
            y=314,
            title="cld-gateway",
            description="conversation-aware proxy",
            accent=theme.runtime,
            theme=theme,
        ),
        _project_node(
            x=666,
            y=439,
            title="claude-assets",
            description="portable agent workflows",
            accent=theme.tooling,
            theme=theme,
        ),
        _text("public work, grouped by where it ships", 930, 522, size=12, fill=theme.muted, anchor="end"),
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "assets",
        help="Directory for generated SVG assets.",
    )
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
