#!/usr/bin/env python3
"""Refresh and render original GitHub profile statistics assets.

The script intentionally stores the last successful public snapshot. A missing
or restricted token cannot turn an unavailable metric into a misleading zero.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://api.github.com/graphql"
REST_API_URL = "https://api.github.com"


class StatsError(RuntimeError):
    """A remote statistics source could not be used safely."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def query_graphql(token: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = Request(
        API_URL,
        data=body,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "tushar2708-profile-stats",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:  # nosec B310 - fixed GitHub API URL
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as error:
        raise StatsError(f"GitHub GraphQL request failed: {error}") from error
    if payload.get("errors"):
        raise StatsError("GitHub GraphQL rejected the statistics query")
    if not isinstance(payload.get("data"), dict):
        raise StatsError("GitHub GraphQL returned no data")
    return payload["data"]


def rest_get_json(token: str, path: str) -> tuple[int, Any | None]:
    """Fetch a GitHub REST endpoint without treating restricted metrics as zero.

    GitHub uses 202 while contributor statistics are being computed and returns
    403/404/422 for metrics that a particular token cannot read.  Those are
    availability states, not numeric values, so callers preserve the last
    verified snapshot instead of replacing it with a partial total.
    """
    request = Request(
        f"{REST_API_URL}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "tushar2708-profile-stats",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:  # nosec B310 - fixed GitHub API URL
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except HTTPError as error:
        if error.code in {202, 204, 403, 404, 422}:
            return error.code, None
        raise StatsError(f"GitHub REST request failed for {path}: {error}") from error
    except (URLError, TimeoutError) as error:
        raise StatsError(f"GitHub REST request failed for {path}: {error}") from error


def contributor_lines(token: str, repository: str, username: str, retries: int = 2) -> int | None:
    """Return GitHub-attributed additions plus deletions for one repository.

    A bounded immediate retry is intentional: Actions runs again tomorrow and
    an unavailable asynchronous GitHub report should not hold a profile job.
    """
    path = f"/repos/{repository}/stats/contributors"
    for _ in range(retries + 1):
        status, payload = rest_get_json(token, path)
        if status == 202:
            continue
        if status != 200 or not isinstance(payload, list):
            return None
        for contributor in payload:
            author = contributor.get("author") or {}
            if str(author.get("login", "")).casefold() != username.casefold():
                continue
            return sum(
                int(week.get("a") or 0) + int(week.get("d") or 0)
                for week in (contributor.get("weeks") or [])
                if isinstance(week, dict)
            )
        return 0
    return None


def aggregate_contributor_lines(token: str, repositories: Iterable[str], username: str) -> tuple[int, int] | None:
    """Aggregate only when every repository supplied an attributable report."""
    total = 0
    count = 0
    for repository in repositories:
        lines = contributor_lines(token, repository, username)
        if lines is None:
            return None
        total += lines
        count += 1
    return total, count


def aggregate_traffic_views(token: str, repositories: Iterable[str]) -> tuple[int, int] | None:
    """Aggregate 14-day traffic only when the token can read the full allowlist."""
    total = 0
    count = 0
    for repository in repositories:
        status, payload = rest_get_json(token, f"/repos/{repository}/traffic/views")
        if status != 200 or not isinstance(payload, dict):
            return None
        value = payload.get("count")
        if not isinstance(value, int):
            return None
        total += value
        count += 1
    return total, count


REPOSITORY_QUERY = """
query ProfileStats($login: String!, $ownedAfter: String, $contributedAfter: String) {
  user(login: $login) {
    repositories(first: 100, after: $ownedAfter, ownerAffiliations: OWNER, isFork: false) {
      nodes { nameWithOwner stargazerCount forkCount languages(first: 100) { edges { size node { name } } } }
      pageInfo { hasNextPage endCursor }
    }
    repositoriesContributedTo(first: 100, after: $contributedAfter, includeUserRepositories: true) {
      nodes { nameWithOwner stargazerCount forkCount languages(first: 100) { edges { size node { name } } } }
      pageInfo { hasNextPage endCursor }
    }
    contributionsCollection { contributionYears }
  }
}
"""

CONTRIBUTION_QUERY = """
query ContributionYear($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { totalContributions }
    }
  }
}
"""


def dedupe_repositories(repositories: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate GitHub nodes without allowing casing differences to double-count."""
    unique: dict[str, dict[str, Any]] = {}
    for repository in repositories:
        name = str(repository.get("nameWithOwner", "")).strip()
        if name:
            unique.setdefault(name.casefold(), repository)
    return list(unique.values())


def aggregate_repositories(repositories: Iterable[dict[str, Any]]) -> tuple[int, int, Counter[str]]:
    stars = 0
    forks = 0
    languages: Counter[str] = Counter()
    for repository in repositories:
        stars += int(repository.get("stargazerCount") or 0)
        forks += int(repository.get("forkCount") or 0)
        edges = (repository.get("languages") or {}).get("edges") or []
        for edge in edges:
            language = str(((edge.get("node") or {}).get("name")) or "").strip()
            size = int(edge.get("size") or 0)
            if language and size > 0:
                languages[language] += size
    return stars, forks, languages


def contribution_total(token: str, username: str, years: Iterable[int]) -> int:
    total = 0
    for year in years:
        data = query_graphql(
            token,
            CONTRIBUTION_QUERY,
            {
                "login": username,
                "from": f"{year}-01-01T00:00:00Z",
                "to": f"{year + 1}-01-01T00:00:00Z",
            },
        )
        total += int(data["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"])
    return total


def fetch_live_snapshot(
    token: str,
    config: dict[str, Any],
    previous_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    username = str(config["username"])
    exclusions = {str(item).casefold() for item in config.get("exclude_repositories", [])}
    owned_after: str | None = None
    contributed_after: str | None = None
    repositories: list[dict[str, Any]] = []
    years: list[int] | None = None

    # Connections are paginated independently: one can finish before the other.
    while True:
        data = query_graphql(
            token,
            REPOSITORY_QUERY,
            {"login": username, "ownedAfter": owned_after, "contributedAfter": contributed_after},
        )
        user = data["user"]
        if user is None:
            raise StatsError(f"GitHub user {username!r} was not found")
        owned = user["repositories"]
        contributed = user["repositoriesContributedTo"]
        repositories.extend(owned.get("nodes") or [])
        repositories.extend(contributed.get("nodes") or [])
        years = [int(year) for year in user["contributionsCollection"]["contributionYears"]]
        owned_info = owned["pageInfo"]
        contributed_info = contributed["pageInfo"]
        owned_after = owned_info["endCursor"] if owned_info["hasNextPage"] else None
        contributed_after = contributed_info["endCursor"] if contributed_info["hasNextPage"] else None
        if owned_after is None and contributed_after is None:
            break

    unique = [repo for repo in dedupe_repositories(repositories) if repo["nameWithOwner"].casefold() not in exclusions]
    stars, forks, languages = aggregate_repositories(unique)
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    snapshot = {
        "generated_at": generated_at,
        "scope": f"Repositories owned by or contributed to by {username}",
        "stars": stars,
        "forks": forks,
        "contributions": contribution_total(token, username, years or []),
        "repositories": len(unique),
        "languages": dict(languages.most_common()),
    }
    repository_names = [str(repository["nameWithOwner"]) for repository in unique]
    line_stats = aggregate_contributor_lines(token, repository_names, username)
    traffic_stats = aggregate_traffic_views(token, config.get("traffic_repositories", []))
    if line_stats is not None:
        snapshot["lines_changed"], snapshot["lines_repositories"] = line_stats
        snapshot["lines_verified_at"] = generated_at
    elif previous_snapshot and "lines_changed" in previous_snapshot:
        snapshot["lines_changed"] = previous_snapshot["lines_changed"]
        snapshot["lines_repositories"] = previous_snapshot.get("lines_repositories")
        snapshot["lines_verified_at"] = previous_snapshot.get("lines_verified_at")
    if traffic_stats is not None:
        snapshot["traffic_views"], snapshot["traffic_repositories"] = traffic_stats
        snapshot["traffic_verified_at"] = generated_at
    elif previous_snapshot and "traffic_views" in previous_snapshot:
        snapshot["traffic_views"] = previous_snapshot["traffic_views"]
        snapshot["traffic_repositories"] = previous_snapshot.get("traffic_repositories")
        snapshot["traffic_verified_at"] = previous_snapshot.get("traffic_verified_at")
    return snapshot


def display_languages(languages: dict[str, int], limit: int) -> list[tuple[str, int, float]]:
    valid = [(str(name), int(size)) for name, size in languages.items() if int(size) > 0]
    total = sum(size for _, size in valid)
    if total <= 0:
        return []
    ordered = sorted(valid, key=lambda item: (-item[1], item[0].casefold()))
    top = ordered[:limit]
    remainder = sum(size for _, size in ordered[limit:])
    if remainder:
        top.append(("Other", remainder))
    return [(name, size, size / total * 100) for name, size in top]


THEMES = {
    "light": {
        "background": "#ffffff", "surface": "#f6f8fa", "text": "#24292f", "muted": "#57606a",
        "rule": "#d0d7de", "accent": "#275dad", "teal": "#0f766e", "gold": "#a15c00",
        "violet": "#6e40c9", "pink": "#bf3989", "rust": "#bf5700", "cyan": "#0969da",
    },
    "dark": {
        "background": "#0d1117", "surface": "#161b22", "text": "#e6edf3", "muted": "#8b949e",
        "rule": "#30363d", "accent": "#79c0ff", "teal": "#56d4dd", "gold": "#e3b341",
        "violet": "#d2a8ff", "pink": "#ff9bce", "rust": "#ffa657", "cyan": "#79c0ff",
    },
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def quantity(value: int) -> str:
    return f"{value:,}"


def verified_day(snapshot: dict[str, Any], field: str) -> str | None:
    """Return a compact, explicit date for a protected metric's source check."""
    value = snapshot.get(field)
    if not isinstance(value, str) or len(value) < 10:
        return None
    return value[:10]


def render_svg(snapshot: dict[str, Any], theme_name: str, language_limit: int) -> str:
    theme = THEMES[theme_name]
    stats: list[tuple[str, str]] = [
        ("Stars across owned + contributed repositories", quantity(int(snapshot.get("stars", 0)))),
        ("Forks across owned + contributed repositories", quantity(int(snapshot.get("forks", 0)))),
        ("All-time GitHub contributions", quantity(int(snapshot.get("contributions", 0)))),
        ("Repositories with contributions", quantity(int(snapshot.get("repositories", 0)))),
    ]
    if isinstance(snapshot.get("lines_changed"), int):
        counted = snapshot.get("lines_repositories")
        suffix = f" ({counted} repositories)" if isinstance(counted, int) else ""
        stats.append((f"GitHub-attributed additions + deletions{suffix}", quantity(snapshot["lines_changed"])))
    else:
        stats.append(("GitHub-attributed additions + deletions", "Token required"))
    if isinstance(snapshot.get("traffic_views"), int):
        counted = snapshot.get("traffic_repositories")
        suffix = f" ({counted} maintained repositories)" if isinstance(counted, int) else ""
        stats.append((f"Repository views · past 14 days{suffix}", quantity(snapshot["traffic_views"])))
    else:
        stats.append(("Repository views · past 14 days", "Token required"))
    optional_verifications = [
        ("lines", verified_day(snapshot, "lines_verified_at")),
        ("views", verified_day(snapshot, "traffic_verified_at")),
    ]
    rendered_verifications = [f"{label} {date}" for label, date in optional_verifications if date]
    languages = display_languages(dict(snapshot.get("languages") or {}), language_limit)
    swatches = [theme["accent"], theme["teal"], theme["gold"], theme["violet"], theme["pink"], theme["rust"], theme["cyan"], theme["muted"], theme["rule"]]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="430" viewBox="0 0 960 430" role="img" aria-labelledby="title desc">',
        '<title id="title">Tushar Dwivedi GitHub field notes</title>',
        '<desc id="desc">A data snapshot of GitHub contribution totals and repository languages.</desc>',
        '<style>.sans{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}</style>',
        f'<rect width="960" height="430" fill="{theme["background"]}"/>',
        f'<rect x="24" y="24" width="912" height="382" rx="16" fill="{theme["surface"]}" stroke="{theme["rule"]}"/>',
        f'<text class="mono" x="56" y="62" font-size="12" font-weight="650" fill="{theme["muted"]}">PROFILE / FIELD NOTES</text>',
        f'<text class="sans" x="56" y="98" font-size="27" font-weight="700" fill="{theme["text"]}">GitHub, in working numbers</text>',
        f'<text class="sans" x="56" y="123" font-size="14" fill="{theme["muted"]}">Public repositories owned by or contributed to by Tushar</text>',
        f'<line x1="492" y1="54" x2="492" y2="374" stroke="{theme["rule"]}"/>',
    ]
    for index, (label, value) in enumerate(stats):
        y = 157 + index * 35
        parts.extend([
            f'<circle cx="62" cy="{y - 5}" r="5" fill="{swatches[index]}"/>',
            f'<text class="sans" x="80" y="{y}" font-size="13" fill="{theme["muted"]}">{esc(label)}</text>',
            f'<text class="sans" x="452" y="{y}" font-size="18" font-weight="700" text-anchor="end" fill="{theme["text"]}">{esc(value)}</text>',
        ])
    parts.extend([
        f'<text class="mono" x="528" y="62" font-size="12" font-weight="650" fill="{theme["muted"]}">REPOSITORY LANGUAGES / FILE SIZE</text>',
        f'<text class="sans" x="528" y="98" font-size="22" font-weight="700" fill="{theme["text"]}">Current language mix</text>',
    ])
    x = 528
    total_width = 365
    for index, (_, _, percentage) in enumerate(languages):
        width = total_width * percentage / 100
        parts.append(f'<rect x="{x:.2f}" y="122" width="{width:.2f}" height="12" rx="4" fill="{swatches[index % len(swatches)]}"/>')
        x += width
    for index, (name, _, percentage) in enumerate(languages):
        column = index % 2
        row = index // 2
        x = 528 + column * 190
        y = 171 + row * 44
        color = swatches[index % len(swatches)]
        parts.extend([
            f'<circle cx="{x}" cy="{y - 5}" r="5" fill="{color}"/>',
            f'<text class="sans" x="{x + 15}" y="{y}" font-size="15" font-weight="650" fill="{theme["text"]}">{esc(name)}</text>',
            f'<text class="sans" x="{x + 15}" y="{y + 18}" font-size="13" fill="{theme["muted"]}">{percentage:.1f}%</text>',
        ])
    generated_at = esc(str(snapshot.get("generated_at", "last verified snapshot")).replace("T", " ").replace("Z", " UTC"))
    optional_status = (
        "protected metrics verified: " + " · ".join(rendered_verifications)
        if rendered_verifications
        else "generated locally from GitHub API data"
    )
    parts.extend([
        f'<line x1="56" y1="374" x2="904" y2="374" stroke="{theme["rule"]}"/>',
        f'<text class="mono" x="56" y="392" font-size="11" fill="{theme["muted"]}">Snapshot: {generated_at}</text>',
        f'<text class="mono" x="904" y="392" text-anchor="end" font-size="11" fill="{theme["muted"]}">{esc(optional_status)}</text>',
        '</svg>',
    ])
    return "\n".join(parts) + "\n"


def render_assets(snapshot: dict[str, Any], config: dict[str, Any], output_dir: Path, check: bool) -> bool:
    output_dir.mkdir(parents=True, exist_ok=True)
    stale = False
    for name in THEMES:
        path = output_dir / f"stats-{name}.svg"
        output = render_svg(snapshot, name, int(config.get("top_language_count", 8)))
        if check:
            stale = stale or not path.exists() or path.read_text(encoding="utf-8") != output
        else:
            path.write_text(output, encoding="utf-8")
    return stale


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "data" / "profile.json")
    parser.add_argument("--cache", type=Path, default=ROOT / "data" / "stats-cache.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "assets")
    parser.add_argument("--refresh", action="store_true", help="Query GitHub using PROFILE_STATS_TOKEN before rendering.")
    parser.add_argument("--check", action="store_true", help="Fail when generated assets are stale.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_json(args.config)["stats"]
    snapshot = load_json(args.cache)
    if args.refresh:
        token = os.environ.get("PROFILE_STATS_TOKEN")
        if not token:
            print("PROFILE_STATS_TOKEN is absent; retaining the last verified statistics snapshot.")
        else:
            try:
                snapshot = fetch_live_snapshot(token, config, snapshot)
                write_json(args.cache, snapshot)
                print("Refreshed GitHub statistics snapshot.")
            except StatsError as error:
                print(f"Could not refresh statistics; retaining last verified snapshot: {error}")
    stale = render_assets(snapshot, config, args.output_dir, args.check)
    if stale:
        print("Statistics SVG assets are stale.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
