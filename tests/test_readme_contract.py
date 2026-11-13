from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


class ReadmeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = README.read_text(encoding="utf-8")

    def test_header_is_text_only_with_clickable_social_links(self) -> None:
        header, _ = self.readme.split("## GitHub field notes", 1)

        self.assertIn("# Tushar Dwivedi", header)
        self.assertNotIn("banner-light.svg", header)
        for url in (
            "https://tushardwivedi.com/",
            "https://www.linkedin.com/in/tushar-dwivedi/",
            "https://bytonomics.com/",
            "https://blog.smritea.ai/",
            "https://dev.to/tushar_bytonomics",
        ):
            self.assertIn(url, header)

    def test_relationship_map_uses_clickable_html_nodes(self) -> None:
        graph, _ = self.readme.split("## Find me", 1)

        self.assertNotIn("topology-light.svg", graph)
        for url in (
            "https://github.com/tushar2708",
            "#ai-memory",
            "#utility-libraries",
            "#developer-tooling-i-have-created-to-make-my-life-easier",
            "https://github.com/SmrutAI/smritea-sdk",
            "https://github.com/SmrutAI/pedantigo",
            "https://github.com/SmrutAI/databridge",
            "https://github.com/Bytonomics/smartcache",
            "https://github.com/tushar2708/conveyor",
            "https://github.com/Bytonomics/kangaroo",
            "https://github.com/Bytonomics/cld-gateway",
            "https://github.com/SmrutAI/opencode-migration",
            "https://github.com/tushar2708/claude-assets",
        ):
            self.assertIn(f'href="{url}"', graph)


if __name__ == "__main__":
    unittest.main()
