#!/usr/bin/env python3
"""Render original light and dark relationship-tree assets for the profile README."""

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
    panel: str
    border: str
    grid: str
    memory: str
    runtime: str
    tooling: str


THEMES = (
    Theme("light", "#1f2937", "#5b6777", "#ffffff", "#f6f8fa", "#d0d7de", "#d8dee4", "#16808b", "#a36a16", "#6956b8"),
    Theme("dark", "#e6edf3", "#9aa7b5", "#0d1117", "#161b22", "#30363d", "#30363d", "#57c5cf", "#e3ad55", "#b8a0ff"),
)


def _text(value: str, x: int, y: int, *, size: int, fill: str, weight: int = 400, anchor: str = "start", family: str = "sans") -> str:
    css_class = "mono" if family == "mono" else "sans"
    return f'<text class="{css_class}" x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(value)}</text>'


def _edge(path: str, accent: str, marker: str) -> str:
    """One relationship edge. Branches intentionally never share a rail."""
    return f'<path d="{path}" fill="none" stroke="{accent}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{marker})"/>'


def _junction(x: int, y: int, accent: str, theme: Theme) -> str:
    return "\n".join((
        f'<circle cx="{x}" cy="{y}" r="9" fill="{theme.surface}" stroke="{accent}" stroke-width="3"/>',
        f'<circle cx="{x}" cy="{y}" r="3" fill="{accent}"/>',
    ))


def _theme_node(x: int, y: int, title: str, subtitle: str, accent: str, theme: Theme) -> str:
    width, height = 196, 64
    left, top = x - width // 2, y - height // 2
    return "\n".join((
        f'<rect x="{left}" y="{top}" width="{width}" height="{height}" rx="12" fill="{theme.panel}" stroke="{accent}" stroke-width="2"/>',
        f'<circle cx="{left + 22}" cy="{top + 23}" r="6" fill="{accent}"/>',
        _text(title, left + 38, top + 27, size=17, fill=theme.text, weight=720),
        _text(subtitle, left + 38, top + 47, size=11, fill=theme.muted, family="mono"),
    ))


def _leaf(x: int, y: int, title: str, subtitle: str, accent: str, theme: Theme) -> str:
    """A compact information-bearing leaf, distinct from a decorative dot."""
    width, height = 150, 54
    left, top = x - width // 2, y - height // 2
    return "\n".join((
        f'<rect x="{left}" y="{top}" width="{width}" height="{height}" rx="9" fill="{theme.surface}" stroke="{theme.border}"/>',
        f'<rect x="{left}" y="{top}" width="4" height="{height}" rx="2" fill="{accent}"/>',
        _text(title, left + 16, top + 22, size=13, fill=theme.text, weight=700),
        _text(subtitle, left + 16, top + 40, size=10, fill=theme.muted, family="mono"),
    ))


def render_svg(theme: Theme) -> str:
    marker, grid = f"arrow-{theme.name}", f"grid-{theme.name}"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="620" viewBox="0 0 960 620" role="img" aria-labelledby="title desc">',
        '<title id="title">Tushar Dwivedi relationship tree</title>',
        '<desc id="desc">A downward relationship tree linking Tushar Dwivedi to AI memory, runtime systems, and developer tooling projects. Each branch is coloured by engineering theme.</desc>',
        '<style>.sans { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }</style>',
        '<defs>',
        f'<pattern id="{grid}" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.7" fill="{theme.grid}"/></pattern>',
        f'<marker id="{marker}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="{theme.muted}"/></marker>',
        '</defs>',
        f'<rect width="960" height="620" fill="url(#{grid})" opacity="0.58"/>',
        _text("relationship tree", 28, 31, size=12, fill=theme.muted, family="mono"),
        _text("coloured by engineering theme", 932, 31, size=12, fill=theme.muted, anchor="end", family="mono"),
        f'<rect x="360" y="53" width="240" height="66" rx="14" fill="{theme.surface}" stroke="{theme.text}" stroke-width="2.5"/>',
        f'<circle cx="389" cy="83" r="7" fill="{theme.text}"/>',
        _text("Tushar Dwivedi", 411, 80, size=19, fill=theme.text, weight=750),
        _text("public work / current map", 411, 102, size=11, fill=theme.muted, family="mono"),
        _edge("M 419 119 C 380 142, 250 139, 204 170", theme.memory, marker),
        _edge("M 480 119 C 480 150, 480 165, 480 191", theme.runtime, marker),
        _edge("M 541 119 C 590 142, 719 139, 758 170", theme.tooling, marker),
        _theme_node(190, 194, "AI memory", "durable context", theme.memory, theme),
        _theme_node(480, 220, "runtime systems", "reliable execution", theme.runtime, theme),
        _theme_node(770, 194, "developer tooling", "agent workflows", theme.tooling, theme),
        _edge("M 190 226 C 187 255, 183 264, 176 282", theme.memory, marker),
        _junction(176, 298, theme.memory, theme),
        _edge("M 168 306 C 132 326, 102 337, 88 361", theme.memory, marker),
        _edge("M 176 307 C 184 360, 192 395, 200 418", theme.memory, marker),
        _edge("M 184 306 C 240 319, 290 326, 318 338", theme.memory, marker),
        _leaf(88, 391, "smritea-sdk", "five-language SDK", theme.memory, theme),
        _leaf(200, 448, "pedantigo", "types + schema", theme.memory, theme),
        _leaf(318, 368, "databridge", "incremental ingestion", theme.memory, theme),
        _edge("M 480 252 C 480 274, 480 289, 480 309", theme.runtime, marker),
        _junction(480, 324, theme.runtime, theme),
        _edge("M 472 332 C 442 362, 421 386, 410 410", theme.runtime, marker),
        _edge("M 488 332 C 530 376, 547 432, 550 474", theme.runtime, marker),
        _leaf(410, 440, "smartcache", "cache semantics", theme.runtime, theme),
        _leaf(550, 504, "conveyor", "concurrent pipelines", theme.runtime, theme),
        _edge("M 770 226 C 771 250, 771 266, 771 286", theme.tooling, marker),
        _junction(771, 302, theme.tooling, theme),
        _edge("M 763 310 C 721 330, 684 347, 664 372", theme.tooling, marker),
        _edge("M 779 310 C 818 333, 851 347, 865 379", theme.tooling, marker),
        _edge("M 776 312 C 771 354, 758 393, 748 447", theme.tooling, marker),
        _junction(748, 462, theme.tooling, theme),
        _edge("M 741 470 C 704 486, 674 500, 662 525", theme.tooling, marker),
        _edge("M 755 470 C 799 488, 840 499, 857 525", theme.tooling, marker),
        _leaf(664, 402, "kangaroo", "task-board plugin", theme.tooling, theme),
        _leaf(865, 409, "cld-gateway", "compatible proxy", theme.tooling, theme),
        _leaf(662, 555, "opencode-migration", "agent migration kit", theme.tooling, theme),
        _leaf(857, 555, "claude-assets", "portable assets", theme.tooling, theme),
        f'<line x1="28" y1="585" x2="932" y2="585" stroke="{theme.border}"/>',
        f'<circle cx="36" cy="602" r="5" fill="{theme.memory}"/>', _text("AI memory", 49, 606, size=11, fill=theme.muted, family="mono"),
        f'<circle cx="166" cy="602" r="5" fill="{theme.runtime}"/>', _text("runtime systems", 179, 606, size=11, fill=theme.muted, family="mono"),
        f'<circle cx="345" cy="602" r="5" fill="{theme.tooling}"/>', _text("developer tooling", 358, 606, size=11, fill=theme.muted, family="mono"),
        _text("theme edges show what connects the work", 932, 606, size=11, fill=theme.muted, anchor="end", family="mono"),
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "assets")
    parser.add_argument("--check", action="store_true", help="Fail when checked-in assets do not match generated output.")
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
        else:
            path.write_text(rendered, encoding="utf-8")
    if stale:
        print("Topology assets are stale: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
