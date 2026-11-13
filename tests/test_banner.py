from __future__ import annotations

import importlib.util
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "render_banner", ROOT / "scripts" / "render_banner.py"
)
assert SPEC and SPEC.loader
render_banner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = render_banner
SPEC.loader.exec_module(render_banner)


class BannerAssetTests(unittest.TestCase):
    def test_portrait_is_a_tracked_local_asset(self) -> None:
        portrait = ROOT / "assets" / "tushar-banner.jpg"
        self.assertTrue(portrait.is_file())
        self.assertGreater(portrait.stat().st_size, 10_000)

    def test_each_banner_is_original_local_svg(self) -> None:
        for theme in render_banner.THEMES:
            with self.subTest(theme=theme.name):
                svg = render_banner.render_svg(theme)
                root = ET.fromstring(svg)
                self.assertEqual(root.attrib["viewBox"], "0 0 960 270")
                self.assertIn('href="data:image/jpeg;base64,', svg)
                self.assertNotIn("https://", svg)
                self.assertNotIn("<script", svg)
                self.assertNotIn("<animate", svg)
                self.assertIsNone(re.search(r"url\(http", svg))


if __name__ == "__main__":
    unittest.main()
