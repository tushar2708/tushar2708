from __future__ import annotations

import importlib.util
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "render_topology", ROOT / "scripts" / "render_topology.py"
)
assert SPEC and SPEC.loader
render_topology = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = render_topology
SPEC.loader.exec_module(render_topology)


class TopologyAssetTests(unittest.TestCase):
    def test_each_theme_is_valid_self_contained_svg(self) -> None:
        for theme in render_topology.THEMES:
            with self.subTest(theme=theme.name):
                svg = render_topology.render_svg(theme)
                root = ET.fromstring(svg)
                self.assertTrue(root.tag.endswith("svg"))
                self.assertEqual(root.attrib["viewBox"], "0 0 960 360")
                self.assertNotIn("<script", svg)
                self.assertNotIn("<animate", svg)
                self.assertIsNone(re.search(r'(?:href|src)="https?://', svg))
                self.assertNotIn("url(http", svg)

    def test_topology_contains_every_public_project(self) -> None:
        svg = render_topology.render_svg(render_topology.THEMES[0])
        for project in (
            "smritea-sdk",
            "pedantigo",
            "databridge",
            "smartcache",
            "cld-gateway",
            "claude-assets",
        ):
            self.assertIn(project, svg)


if __name__ == "__main__":
    unittest.main()
