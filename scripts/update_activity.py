#!/usr/bin/env python3
"""Refresh generated release and writing sections in the profile README."""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import html
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Iterable


BUILD_SECTION = "PROFILE:BUILD"
WRITE_SECTION = "PROFILE:WRITE"
USER_AGENT = "tushar2708-profile-updater/1.0"


class SourceError(RuntimeError):
    """Raised when an upstream source cannot be used safely."""


@dataclass(frozen=True)
class Release:
    repository: str
    label: str
    url: str
    published: dt.datetime


@dataclass(frozen=True)
class Article:
    title: str
    url: str
    source: str
    priority: int
    published: dt.datetime


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--config", type=Path, default=Path("data/profile.json"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Do not write; exit 1 when the README would change.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write; print the candidate README to stdout.",
    )
    return parser.parse_args(argv)


def load_config(path: Path) -> dict[str, Any]:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
        activity = config["activity"]
        activity["release_repositories"]
        activity["feeds"]
        activity["release_limit"]
        activity["article_limit"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise SourceError(f"invalid profile configuration: {exc}") from exc
    return config


def fetch_bytes(url: str, *, accept: str, token: str | None = None) -> bytes:
    headers = {"Accept": accept, "User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SourceError(f"could not fetch {url}: {exc}") from exc


def parse_datetime(value: str | None) -> dt.datetime:
    if not value:
        raise ValueError("missing publication date")
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def is_allowed_https(url: str, allowed_hosts: Iterable[str]) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    allowed = {item.lower().rstrip(".") for item in allowed_hosts}
    return parsed.scheme == "https" and host in allowed and not parsed.username


def sanitize_text(value: str) -> str:
    """Return one safe Markdown link-label line from untrusted text."""

    text = html.unescape(value)
    text = re.sub(r"<[^>]*>", "", text)
    text = " ".join(text.split())
    text = text.replace("\\", "\\\\")
    for character in "`*_[]<>":
        text = text.replace(character, f"\\{character}")
    return text


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", html.unescape(value)).casefold()
    return "".join(character for character in value if character.isalnum())


def normalize_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = [(key, val) for key, val in query if not key.lower().startswith("utm_")]
    return urllib.parse.urlunsplit(
        (
            parsed.scheme.lower(),
            (parsed.hostname or "").lower(),
            parsed.path.rstrip("/"),
            urllib.parse.urlencode(query),
            "",
        )
    )


def parse_releases(payload: bytes, repository: str) -> list[Release]:
    try:
        records = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SourceError(f"invalid GitHub response for {repository}: {exc}") from exc
    if not isinstance(records, list):
        raise SourceError(f"unexpected GitHub response for {repository}")

    releases: list[Release] = []
    for record in records:
        if not isinstance(record, dict) or record.get("draft") or record.get("prerelease"):
            continue
        url = str(record.get("html_url", ""))
        if not is_allowed_https(url, ["github.com"]):
            continue
        try:
            published = parse_datetime(record.get("published_at"))
        except (TypeError, ValueError):
            continue
        label = str(record.get("name") or record.get("tag_name") or "release")
        releases.append(
            Release(
                repository=repository,
                label=label,
                url=url,
                published=published,
            )
        )
    return releases


def fetch_releases(repositories: Iterable[str], token: str | None) -> list[Release]:
    releases: list[Release] = []
    for repository in repositories:
        encoded = urllib.parse.quote(repository, safe="/")
        url = f"https://api.github.com/repos/{encoded}/releases?per_page=20"
        payload = fetch_bytes(
            url,
            accept="application/vnd.github+json",
            token=token,
        )
        releases.extend(parse_releases(payload, repository))
    return releases


def child_text(element: ET.Element, local_name: str) -> str:
    for child in element:
        if child.tag.rsplit("}", 1)[-1] == local_name:
            return (child.text or "").strip()
    return ""


def parse_feed(payload: bytes, feed: dict[str, Any]) -> list[Article]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise SourceError(f"invalid RSS from {feed['name']}: {exc}") from exc

    articles: list[Article] = []
    items = [element for element in root.iter() if element.tag.rsplit("}", 1)[-1] in {"item", "entry"}]
    for item in items:
        title = child_text(item, "title")
        link = child_text(item, "link")
        if not link:
            for child in item:
                if child.tag.rsplit("}", 1)[-1] == "link" and child.get("href"):
                    link = child.get("href", "")
                    break
        date_value = (
            child_text(item, "pubDate")
            or child_text(item, "published")
            or child_text(item, "updated")
        )
        if not title or not is_allowed_https(link, feed["allowed_hosts"]):
            continue
        try:
            published = parse_datetime(date_value)
        except (TypeError, ValueError):
            continue
        articles.append(
            Article(
                title=title,
                url=normalize_url(link),
                source=str(feed["name"]),
                priority=int(feed.get("priority", 100)),
                published=published,
            )
        )
    return articles


def fetch_articles(feeds: Iterable[dict[str, Any]]) -> list[Article]:
    articles: list[Article] = []
    for feed in feeds:
        url = str(feed["url"])
        if not is_allowed_https(url, feed["allowed_hosts"]):
            raise SourceError(f"unsafe feed URL for {feed['name']}: {url}")
        payload = fetch_bytes(url, accept="application/rss+xml, application/atom+xml, application/xml, text/xml")
        articles.extend(parse_feed(payload, feed))
    return articles


def dedupe_articles(articles: Iterable[Article]) -> list[Article]:
    """Prefer the lowest-priority source before ordering unique posts by date."""

    preferred = sorted(articles, key=lambda item: (item.priority, -item.published.timestamp()))
    seen_titles: set[str] = set()
    seen_urls: set[str] = set()
    unique: list[Article] = []
    for article in preferred:
        title_key = normalize_title(article.title)
        url_key = normalize_url(article.url)
        if not title_key or title_key in seen_titles or url_key in seen_urls:
            continue
        seen_titles.add(title_key)
        seen_urls.add(url_key)
        unique.append(article)
    return sorted(unique, key=lambda item: item.published, reverse=True)


def render_releases(releases: Iterable[Release], limit: int) -> str:
    selected = sorted(releases, key=lambda item: item.published, reverse=True)[:limit]
    if not selected:
        return "_No published releases yet._"
    return "\n".join(
        f"- [{sanitize_text(item.repository)} — {sanitize_text(item.label)}]({item.url}) "
        f"<sub>{item.published.date().isoformat()}</sub>"
        for item in selected
    )


def render_articles(articles: Iterable[Article], limit: int) -> str:
    selected = dedupe_articles(articles)[:limit]
    if not selected:
        return "_No articles published yet._"
    return "\n".join(
        f"- [{sanitize_text(item.title)}]({item.url}) "
        f"<sub>{sanitize_text(item.source)} · {item.published.date().isoformat()}</sub>"
        for item in selected
    )


def replace_section(document: str, section: str, rendered: str) -> str:
    start = f"<!-- {section}:START -->"
    end = f"<!-- {section}:END -->"
    start_index = document.find(start)
    end_index = document.find(end)
    if start_index < 0 or end_index < 0 or end_index < start_index:
        raise SourceError(f"README is missing valid {section} markers")
    content_start = start_index + len(start)
    return document[:content_start] + "\n" + rendered.rstrip() + "\n" + document[end_index:]


def emit_warning(message: str) -> None:
    prefix = "::warning::" if os.environ.get("GITHUB_ACTIONS") else "warning: "
    print(f"{prefix}{message}", file=sys.stderr)


def refresh_document(
    document: str,
    activity: dict[str, Any],
    *,
    token: str | None,
) -> tuple[str, list[str]]:
    updated = document
    warnings: list[str] = []

    try:
        releases = fetch_releases(activity["release_repositories"], token)
        updated = replace_section(
            updated,
            BUILD_SECTION,
            render_releases(releases, int(activity["release_limit"])),
        )
    except (SourceError, KeyError, TypeError, ValueError) as exc:
        warnings.append(f"BUILD was preserved: {exc}")

    try:
        articles = fetch_articles(activity["feeds"])
        updated = replace_section(
            updated,
            WRITE_SECTION,
            render_articles(articles, int(activity["article_limit"])),
        )
    except (SourceError, KeyError, TypeError, ValueError) as exc:
        warnings.append(f"WRITE was preserved: {exc}")

    return updated, warnings


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        original = args.readme.read_text(encoding="utf-8")
    except (OSError, SourceError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    updated, warnings = refresh_document(
        original,
        config["activity"],
        token=os.environ.get("GITHUB_TOKEN"),
    )
    for warning in warnings:
        emit_warning(warning)

    if args.dry_run:
        print(updated, end="")
        return 0
    if args.check:
        return 1 if updated != original else 0
    if updated != original:
        args.readme.write_text(updated, encoding="utf-8")
        print(f"updated {args.readme}")
    else:
        print("profile activity is already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
