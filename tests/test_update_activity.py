from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_activity as updater  # noqa: E402


FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def readme(build: str = "old build", write: str = "old write") -> str:
    return (
        "# Profile\n\n"
        "Before\n"
        "<!-- PROFILE:BUILD:START -->\n"
        f"{build}\n"
        "<!-- PROFILE:BUILD:END -->\n\n"
        "Between\n"
        "<!-- PROFILE:WRITE:START -->\n"
        f"{write}\n"
        "<!-- PROFILE:WRITE:END -->\n"
        "After\n"
    )


class ReleaseTests(unittest.TestCase):
    def test_parse_releases_keeps_only_safe_stable_releases(self) -> None:
        releases = updater.parse_releases(fixture("releases.json"), "SmrutAI/pedantigo")

        self.assertEqual([release.label for release in releases], ["Pedantigo 2.0", "Pedantigo 1.9"])
        self.assertTrue(all(release.url.startswith("https://github.com/") for release in releases))

    def test_render_releases_sorts_globally_and_limits_output(self) -> None:
        base = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
        releases = [
            updater.Release("org/older", "v1", "https://github.com/org/older/releases/tag/v1", base),
            updater.Release("org/newer", "v2", "https://github.com/org/newer/releases/tag/v2", base + dt.timedelta(days=2)),
        ]

        rendered = updater.render_releases(releases, 1)

        self.assertIn("org/newer", rendered)
        self.assertNotIn("org/older", rendered)

    def test_render_releases_shows_only_the_newest_release_per_repository(self) -> None:
        base = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
        releases = [
            updater.Release(
                "Bytonomics/cld-gateway",
                "v1.1.4",
                "https://github.com/Bytonomics/cld-gateway/releases/tag/v1.1.4",
                base + dt.timedelta(days=1),
            ),
            updater.Release(
                "Bytonomics/cld-gateway",
                "v1.1.5",
                "https://github.com/Bytonomics/cld-gateway/releases/tag/v1.1.5",
                base + dt.timedelta(days=3),
            ),
            updater.Release(
                "Bytonomics/smartcache",
                "v0.4.0",
                "https://github.com/Bytonomics/smartcache/releases/tag/v0.4.0",
                base + dt.timedelta(days=2),
            ),
            updater.Release(
                "SmrutAI/pedantigo",
                "v2.0.0",
                "https://github.com/SmrutAI/pedantigo/releases/tag/v2.0.0",
                base,
            ),
        ]

        rendered = updater.render_releases(releases, 3)

        self.assertEqual(rendered.count("<strong>Bytonomics/cld-gateway</strong>"), 1)
        self.assertIn("v1.1.5", rendered)
        self.assertNotIn("v1.1.4", rendered)
        self.assertIn("Bytonomics/smartcache", rendered)
        self.assertIn("SmrutAI/pedantigo", rendered)
        self.assertIn("<table>", rendered)
        self.assertIn("Latest stable public release", rendered)
        self.assertEqual(rendered.count("<tr>"), 3)


class FeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.smritea = {
            "name": "Smritea Blog",
            "allowed_hosts": ["blog.smritea.ai"],
            "priority": 0,
        }
        self.dev = {
            "name": "DEV",
            "allowed_hosts": ["dev.to"],
            "priority": 1,
        }

    def test_parse_feed_rejects_links_outside_the_allowlist(self) -> None:
        articles = updater.parse_feed(fixture("smritea.xml"), self.smritea)

        self.assertEqual(len(articles), 2)
        self.assertTrue(all(article.url.startswith("https://blog.smritea.ai/") for article in articles))

    def test_cross_post_dedupe_prefers_smritea_and_orders_by_date(self) -> None:
        articles = updater.parse_feed(fixture("smritea.xml"), self.smritea)
        articles += updater.parse_feed(fixture("dev.xml"), self.dev)

        unique = updater.dedupe_articles(articles)

        self.assertEqual(len(unique), 3)
        caching = [article for article in unique if "caching" in article.title][0]
        self.assertEqual(caching.source, "Smritea Blog")
        self.assertEqual(unique[0].title, "Building [safe] profile automation")
        self.assertNotIn("utm_source", " ".join(article.url for article in unique))

    def test_rendered_untrusted_title_cannot_break_the_markdown_link(self) -> None:
        article = updater.Article(
            title="A [link] <script>bad()</script>",
            url="https://dev.to/tushar_bytonomics/safe",
            source="DEV",
            priority=1,
            published=dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc),
        )

        rendered = updater.render_articles(
            [article],
            1,
            image_hosts_by_source={"Smritea Blog": ["blog.smritea.ai"]},
        )

        self.assertNotIn("<script>", rendered)
        self.assertIn("A [link] bad()", rendered)
        self.assertIn("<table>", rendered)

    @mock.patch("update_activity.fetch_bytes")
    def test_open_graph_image_is_limited_to_configured_hosts(self, fetch_bytes: mock.Mock) -> None:
        article = updater.Article(
            "Safe post",
            "https://blog.smritea.ai/safe-post",
            "Smritea Blog",
            0,
            dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc),
        )
        feed = {
            "allowed_hosts": ["blog.smritea.ai"],
            "image_hosts": ["blog.smritea.ai"],
            "fetch_open_graph_image": True,
        }
        fetch_bytes.return_value = b'<meta property="og:image" content="https://blog.smritea.ai/safe-post/og.png?utm_source=rss">'

        image = updater.fetch_open_graph_image(article, feed)

        self.assertEqual(image, "https://blog.smritea.ai/safe-post/og.png")
        fetch_bytes.return_value = b'<meta property="og:image" content="https://evil.example/image.png">'
        self.assertIsNone(updater.fetch_open_graph_image(article, feed))

    def test_rich_article_row_escapes_summary_and_uses_safe_thumbnail(self) -> None:
        article = updater.Article(
            "A <title>",
            "https://blog.smritea.ai/safe",
            "Smritea Blog",
            0,
            dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc),
            summary="Summary with <b>markup</b> & details",
            image_url="https://blog.smritea.ai/safe/og.png",
        )

        rendered = updater.render_articles(
            [article],
            1,
            image_hosts_by_source={"Smritea Blog": ["blog.smritea.ai"]},
        )

        self.assertIn('width="180"', rendered)
        self.assertIn('alt="A"', rendered)
        self.assertNotIn("<title>", rendered)
        self.assertIn("Summary with markup &amp; details", rendered)
        self.assertNotIn("<b>markup</b>", rendered)

    def test_article_image_from_an_unconfigured_host_falls_back_to_text_only(self) -> None:
        article = updater.Article(
            "Unconfigured image",
            "https://blog.smritea.ai/safe",
            "Smritea Blog",
            0,
            dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc),
            image_url="https://evil.example/image.png",
        )

        rendered = updater.render_articles(
            [article],
            1,
            image_hosts_by_source={"Smritea Blog": ["blog.smritea.ai"]},
        )

        self.assertNotIn("<img", rendered)
        self.assertIn("Unconfigured image", rendered)

    def test_article_without_image_uses_text_only_row(self) -> None:
        article = updater.Article(
            "Text only",
            "https://dev.to/tushar_bytonomics/text-only",
            "DEV",
            1,
            dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc),
            summary="A useful update.",
        )

        rendered = updater.render_articles([article], 1)

        self.assertIn("A useful update.", rendered)
        self.assertNotIn('width="180"', rendered)


class DocumentTests(unittest.TestCase):
    def test_replace_section_changes_only_the_requested_marker_block(self) -> None:
        original = readme()

        updated = updater.replace_section(original, updater.BUILD_SECTION, "new build")

        self.assertIn("new build", updated)
        self.assertNotIn("old build", updated)
        self.assertIn("old write", updated)
        self.assertTrue(updated.startswith("# Profile\n\nBefore"))
        self.assertTrue(updated.endswith("After\n"))

    @mock.patch("update_activity.fetch_articles")
    @mock.patch("update_activity.fetch_releases")
    def test_release_failure_preserves_build_but_allows_write_refresh(
        self,
        fetch_releases: mock.Mock,
        fetch_articles: mock.Mock,
    ) -> None:
        fetch_releases.side_effect = updater.SourceError("GitHub unavailable")
        fetch_articles.return_value = [
            updater.Article(
                "Fresh article",
                "https://blog.smritea.ai/fresh",
                "Smritea Blog",
                0,
                dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc),
            )
        ]
        activity = {
            "release_repositories": ["org/repo"],
            "release_limit": 3,
            "feeds": [],
            "article_limit": 3,
        }

        updated, warnings = updater.refresh_document(readme(), activity, token=None)

        self.assertIn("old build", updated)
        self.assertIn("Fresh article", updated)
        self.assertEqual(len(warnings), 1)
        self.assertIn("BUILD was preserved", warnings[0])

    @mock.patch("update_activity.fetch_articles")
    @mock.patch("update_activity.fetch_releases")
    def test_feed_failure_preserves_write_but_allows_build_refresh(
        self,
        fetch_releases: mock.Mock,
        fetch_articles: mock.Mock,
    ) -> None:
        fetch_releases.return_value = [
            updater.Release(
                "org/repo",
                "v1.0.0",
                "https://github.com/org/repo/releases/tag/v1.0.0",
                dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc),
            )
        ]
        fetch_articles.side_effect = updater.SourceError("RSS unavailable")
        activity = {
            "release_repositories": [],
            "release_limit": 3,
            "feeds": [{"name": "broken"}],
            "article_limit": 3,
        }

        updated, warnings = updater.refresh_document(readme(), activity, token=None)

        self.assertIn("v1.0.0", updated)
        self.assertIn("old write", updated)
        self.assertEqual(len(warnings), 1)
        self.assertIn("WRITE was preserved", warnings[0])

    @mock.patch("update_activity.refresh_document")
    def test_check_mode_reports_no_change_without_writing(self, refresh: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readme_path = root / "README.md"
            config_path = root / "profile.json"
            original = readme()
            readme_path.write_text(original, encoding="utf-8")
            config_path.write_text(json.dumps({"activity": {"release_repositories": [], "feeds": [], "release_limit": 3, "article_limit": 3}}), encoding="utf-8")
            refresh.return_value = (original, [])

            result = updater.main(["--readme", str(readme_path), "--config", str(config_path), "--check"])

            self.assertEqual(result, 0)
            self.assertEqual(readme_path.read_text(encoding="utf-8"), original)

    @mock.patch("update_activity.refresh_document")
    def test_check_mode_reports_pending_change_without_writing(self, refresh: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readme_path = root / "README.md"
            config_path = root / "profile.json"
            original = readme()
            readme_path.write_text(original, encoding="utf-8")
            config_path.write_text(json.dumps({"activity": {"release_repositories": [], "feeds": [], "release_limit": 3, "article_limit": 3}}), encoding="utf-8")
            refresh.return_value = (original + "changed", [])

            result = updater.main(["--readme", str(readme_path), "--config", str(config_path), "--check"])

            self.assertEqual(result, 1)
            self.assertEqual(readme_path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
