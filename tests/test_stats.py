from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_stats as stats  # noqa: E402


class AggregationTests(unittest.TestCase):
    def test_dedupe_repositories_is_case_insensitive(self) -> None:
        repositories = stats.dedupe_repositories(
            [
                {"nameWithOwner": "SmrutAI/Pedantigo", "stargazerCount": 2},
                {"nameWithOwner": "smrutai/pedantigo", "stargazerCount": 99},
                {"nameWithOwner": "Bytonomics/smartcache", "stargazerCount": 4},
            ]
        )

        self.assertEqual([item["nameWithOwner"] for item in repositories], ["SmrutAI/Pedantigo", "Bytonomics/smartcache"])

    def test_aggregate_repositories_sums_languages_by_byte_size(self) -> None:
        repositories = [
            {
                "stargazerCount": 4,
                "forkCount": 2,
                "languages": {"edges": [{"size": 10, "node": {"name": "Go"}}, {"size": 3, "node": {"name": "Python"}}]},
            },
            {
                "stargazerCount": 1,
                "forkCount": 0,
                "languages": {"edges": [{"size": 7, "node": {"name": "Go"}}]},
            },
        ]

        stars, forks, languages = stats.aggregate_repositories(repositories)

        self.assertEqual((stars, forks), (5, 2))
        self.assertEqual(languages, {"Go": 17, "Python": 3})

    def test_display_languages_uses_other_and_totals_one_hundred_percent(self) -> None:
        languages = stats.display_languages({"Go": 50, "Python": 30, "Rust": 20}, 2)

        self.assertEqual([item[0] for item in languages], ["Go", "Python", "Other"])
        self.assertAlmostEqual(sum(item[2] for item in languages), 100.0)

    @mock.patch("update_stats.rest_get_json")
    def test_contributor_lines_retries_a_pending_report(self, rest_get_json: mock.Mock) -> None:
        rest_get_json.side_effect = [
            (202, None),
            (
                200,
                [
                    {
                        "author": {"login": "tushar2708"},
                        "weeks": [{"a": 7, "d": 3}, {"a": 2, "d": 0}],
                    }
                ],
            ),
        ]

        self.assertEqual(stats.contributor_lines("token", "SmrutAI/pedantigo", "tushar2708"), 12)
        self.assertEqual(rest_get_json.call_count, 2)

    @mock.patch("update_stats.rest_get_json")
    def test_line_and_traffic_totals_do_not_accept_partial_access(self, rest_get_json: mock.Mock) -> None:
        rest_get_json.side_effect = [
            (200, [{"author": {"login": "tushar2708"}, "weeks": [{"a": 3, "d": 1}]}]),
            (403, None),
        ]

        self.assertIsNone(
            stats.aggregate_contributor_lines("token", ["SmrutAI/pedantigo", "Bytonomics/smartcache"], "tushar2708")
        )

        rest_get_json.side_effect = [
            (200, {"count": 11}),
            (404, None),
        ]
        self.assertIsNone(stats.aggregate_traffic_views("token", ["SmrutAI/pedantigo", "Bytonomics/smartcache"]))

    @mock.patch("update_stats.rest_get_json")
    def test_traffic_views_counts_the_explicit_allowlist(self, rest_get_json: mock.Mock) -> None:
        rest_get_json.side_effect = [(200, {"count": 11}), (200, {"count": 7})]

        self.assertEqual(
            stats.aggregate_traffic_views("token", ["SmrutAI/pedantigo", "Bytonomics/smartcache"]),
            (18, 2),
        )


class RenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = {
            "generated_at": "2026-11-13T00:00:00Z",
            "stars": 77,
            "forks": 19,
            "contributions": 5084,
            "repositories": 71,
            "languages": {"Go": 20, "Python": 10, "<unsafe>": 5},
        }

    def test_rendering_escapes_api_derived_language_names(self) -> None:
        rendered = stats.render_svg(self.snapshot, "light", 8)

        self.assertIn("&lt;unsafe&gt;", rendered)
        self.assertNotIn("<unsafe>", rendered)
        self.assertNotIn("foreignObject", rendered)

    def test_themes_render_the_same_verified_values(self) -> None:
        light = stats.render_svg(self.snapshot, "light", 8)
        dark = stats.render_svg(self.snapshot, "dark", 8)

        for value in ("5,084", "77", "19", "71", "Go", "Python"):
            self.assertIn(value, light)
            self.assertIn(value, dark)

    def test_rendering_marks_metrics_requiring_a_token(self) -> None:
        rendered = stats.render_svg(self.snapshot, "light", 8)

        self.assertEqual(rendered.count("Token required"), 2)

    def test_rendering_includes_verified_optional_metrics(self) -> None:
        snapshot = {
            **self.snapshot,
            "lines_changed": 4321,
            "lines_repositories": 2,
            "lines_verified_at": "2026-11-12T00:00:00Z",
            "traffic_views": 765,
            "traffic_repositories": 3,
            "traffic_verified_at": "2026-11-11T00:00:00Z",
        }
        rendered = stats.render_svg(snapshot, "dark", 8)

        self.assertIn("4,321", rendered)
        self.assertIn("765", rendered)
        self.assertIn("2 repositories", rendered)
        self.assertIn("3 maintained repositories", rendered)
        self.assertIn("protected metrics verified: lines 2026-11-12 · views 2026-11-11", rendered)

    def test_check_mode_detects_stale_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "profile.json"
            cache = root / "stats.json"
            assets = root / "assets"
            config.write_text(json.dumps({"stats": {"top_language_count": 8}}), encoding="utf-8")
            cache.write_text(json.dumps(self.snapshot), encoding="utf-8")

            self.assertEqual(stats.main(["--config", str(config), "--cache", str(cache), "--output-dir", str(assets)]), 0)
            self.assertEqual(stats.main(["--config", str(config), "--cache", str(cache), "--output-dir", str(assets), "--check"]), 0)
            (assets / "stats-light.svg").write_text("stale", encoding="utf-8")
            self.assertEqual(stats.main(["--config", str(config), "--cache", str(cache), "--output-dir", str(assets), "--check"]), 1)

    @mock.patch("update_stats.fetch_live_snapshot")
    def test_missing_token_preserves_last_verified_cache(self, fetch_live_snapshot: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "profile.json"
            cache = root / "stats.json"
            assets = root / "assets"
            config.write_text(json.dumps({"stats": {"top_language_count": 8}}), encoding="utf-8")
            cache.write_text(json.dumps(self.snapshot), encoding="utf-8")
            with mock.patch.dict("os.environ", {}, clear=True):
                self.assertEqual(stats.main(["--config", str(config), "--cache", str(cache), "--output-dir", str(assets), "--refresh"]), 0)

            self.assertEqual(json.loads(cache.read_text(encoding="utf-8")), self.snapshot)
            fetch_live_snapshot.assert_not_called()


if __name__ == "__main__":
    unittest.main()
