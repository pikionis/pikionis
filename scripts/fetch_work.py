#!/usr/bin/env python3
"""Collects what I am working on into data/work.json, so the README never falls behind.

  repos     my public repositories, newest push first (GitHub API)
  projects  the projects on onehublabs.com, read from the site's own repo (src/content/projects/*.md)

A new public repo, or a new project file on the site, shows up in the README on the next run.
Anything that can't be reached keeps what was saved last time.

    GITHUB_TOKEN=...  optional, raises the API rate limit (the Action passes its own)
    SITE_DIR=path     read the projects from a local checkout of the site instead of the API
"""
import base64
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "work.json"
PROFILE = json.loads((ROOT / "data" / "profile.json").read_text())
USER = sys.argv[1] if len(sys.argv) > 1 else "pikionis"
API = "https://api.github.com"


def get(path):
    headers = {"User-Agent": "profile-readme-cards", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(API + path, headers=headers), timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def first_paragraph(markdown):
    """The first line of prose in a README: not a heading, badge, image, quote, list or HTML."""
    for block in re.split(r"\n\s*\n", markdown):
        line = " ".join(block.split())
        if line and not re.match(r"^(#|!\[|\[!\[|<|>|-|\*|\||```|=+$)", line):
            return re.sub(r"[*_`]|\[([^\]]+)\]\([^)]*\)", lambda m: m[1] or "", line)[:260]
    return ""


def repos():
    found = []
    for repo in get(f"/users/{USER}/repos?per_page=100&sort=pushed&type=owner"):
        if repo["fork"] or repo["archived"] or repo["private"] or not repo["size"]:
            continue  # size 0 = nothing pushed yet
        description = repo["description"] or ""
        if not description and repo["name"] not in PROFILE["repo_overrides"]:
            try:
                readme = get(f"/repos/{USER}/{repo['name']}/readme")
                description = first_paragraph(base64.b64decode(readme["content"]).decode("utf-8", "replace"))
            except Exception:  # noqa: BLE001 - no README is fine
                pass
        languages = []
        if repo["name"] not in PROFILE["exclude_repos"]:
            try:
                languages = list(get(f"/repos/{USER}/{repo['name']}/languages"))[:3]  # the most used first
            except Exception:  # noqa: BLE001 - a card without them is fine
                pass
        found.append({"name": repo["name"], "description": description, "language": repo["language"] or "",
                      "languages": languages, "topics": repo.get("topics", []), "pushed_at": repo["pushed_at"],
                      "url": repo["html_url"]})
    return found


def front_matter(markdown):
    """The handful of front-matter fields the README shows; no YAML library needed for these."""
    head = re.match(r"^---\n(.*?)\n---", markdown, re.S)
    fields = {}
    for line in (head[1] if head else "").splitlines():
        pair = re.match(r'^(\w+):\s*(.+?)\s*$', line)
        if not pair:
            continue
        key, value = pair[1], pair[2]
        if value.startswith("["):
            fields[key] = re.findall(r'"([^"]*)"|\'([^\']*)\'|([^,\[\]\s][^,\[\]]*)', value)
            fields[key] = [next(part for part in item if part).strip() for item in fields[key]]
        else:
            fields[key] = value.strip("\"'")
    return fields


def projects():
    files = {}
    site_dir = os.environ.get("SITE_DIR")
    if site_dir:
        for path in sorted((Path(site_dir) / "src/content/projects").glob("[!_]*.md")):
            files[path.stem] = path.read_text(encoding="utf-8")
    else:
        for entry in get(f"/repos/{PROFILE['site_repo']}/contents/src/content/projects"):
            if entry["type"] == "file" and entry["name"].endswith(".md") and not entry["name"].startswith("_"):
                content = get(f"/repos/{PROFILE['site_repo']}/contents/{entry['path']}")
                files[entry["name"][:-3]] = base64.b64decode(content["content"]).decode("utf-8")
    found = []
    for slug, markdown in files.items():
        fields = front_matter(markdown)
        if fields.get("draft") == "true" or not fields.get("title"):
            continue
        found.append({"slug": slug, "title": fields["title"], "summary": fields.get("summary", ""),
                      "badge": fields.get("badge", ""), "stack": fields.get("stack", []),
                      "order": float(fields.get("order", 0) or 0)})
    return sorted(found, key=lambda p: (p["order"], p["title"]))


saved = json.loads(OUT.read_text()) if OUT.exists() else {"repos": [], "projects": []}
for key, fetch in (("repos", repos), ("projects", projects)):
    try:
        fresh = fetch()
        if not fresh:
            raise RuntimeError("nothing came back")
        saved[key] = fresh
        print(f"{key}: {len(fresh)}")
    except Exception as error:  # noqa: BLE001 - any failure keeps the saved list
        print(f"{key}: kept the saved list ({error})")
OUT.write_text(json.dumps(saved, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
