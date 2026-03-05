#!/usr/bin/env python3
"""Fetch public GitHub repo stats + traffic and generate a leaderboard."""

import json
import subprocess
import sys

USERNAME = "amirouche"


def gh_api(endpoint):
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def fetch_all_public_repos():
    repos = []
    page = 1
    while True:
        data = gh_api(f"/users/{USERNAME}/repos?type=owner&per_page=100&page={page}")
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def fetch_commit_count(repo_name):
    # Use the participation stats (last year, per week)
    data = gh_api(f"/repos/{USERNAME}/{repo_name}/contributors")
    if not data:
        return 0
    return sum(c.get("contributions", 0) for c in data)


def fetch_traffic(repo_name):
    base = f"/repos/{USERNAME}/{repo_name}/traffic"
    views = gh_api(f"{base}/views") or {}
    clones = gh_api(f"{base}/clones") or {}
    return {
        "views": views.get("count", 0),
        "views_unique": views.get("uniques", 0),
        "clones": clones.get("count", 0),
        "clones_unique": clones.get("uniques", 0),
    }


def pick_highlight(metrics):
    """Pick the most standout metric for a repo relative to its other stats."""
    candidates = [
        ("clones", metrics["clones"], "{} clones in 14 days"),
        ("stars", metrics["stars"], "{} stars"),
        ("commits", metrics["commits"], "{} commits"),
        ("views", metrics["views"], "{} views in 14 days"),
        ("forks", metrics["forks"], "{} forks"),
        ("open_issues", metrics["open_issues"], "{} open issues"),
    ]
    # Pick the metric where this repo has the highest value, preferring rarer signals
    best = max(candidates, key=lambda c: c[1])
    if best[1] == 0:
        lang = metrics.get("language", "N/A")
        return f"Written in {lang}"
    return best[2].format(best[1])


def compute_score(m):
    return (
        m["stars"] * 50
        + m["forks"] * 40
        + m["commits"] * 5
        + m["clones"] * 2
        + m["views"] * 1
    )


def main():
    repos = fetch_all_public_repos()
    repos = [r for r in repos if not r["fork"]]

    enriched = []
    for r in repos:
        name = r["name"]
        print(f"Fetching data for {name}...", file=sys.stderr)
        traffic = fetch_traffic(name)
        commits = fetch_commit_count(name)
        metrics = {
            "name": name,
            "url": r["html_url"],
            "description": r["description"] or "No description.",
            "language": r["language"] or "N/A",
            "stars": r["stargazers_count"],
            "forks": r["forks_count"],
            "open_issues": r["open_issues_count"],
            "commits": commits,
            **traffic,
        }
        metrics["score"] = compute_score(metrics)
        metrics["highlight"] = pick_highlight(metrics)
        enriched.append(metrics)

    enriched.sort(key=lambda m: m["score"], reverse=True)
    top = enriched[:5]

    lines = [
        f"# Leaderboard: {USERNAME}'s Top Repositories",
        "",
        f"*{len(enriched)} owned public repositories scored and ranked.*",
        "",
        "**Scoring:** stars x50 + forks x40 + commits x5 + clones x2 + views x1",
        "",
        "| Rank | Repository | Language | Score | Highlight |",
        "|------|-----------|----------|------:|-----------|",
    ]
    for i, m in enumerate(top, 1):
        lines.append(
            f"| {i} | [{m['name']}]({m['url']}) | {m['language']} "
            f"| {m['score']} | {m['highlight']} |"
        )

    lines.append("")

    output = "\n".join(lines)
    print(output)

    with open("top5_repos.md", "w") as f:
        f.write(output + "\n")
    print(f"\nSaved to top5_repos.md", file=sys.stderr)


if __name__ == "__main__":
    main()
