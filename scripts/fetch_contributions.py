#!/usr/bin/env python3
"""Pulls the public GitHub contribution calendar into data/contributions.json.

Same source and shape as scripts/github.mjs in the onehublabs.com repo:
{"user", "endDate", "counts": one number per day, oldest first}.
If GitHub can't be reached, or the page changed, the saved file is kept.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "pikionis"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"

try:
    request = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                     headers={"User-Agent": "profile-readme-cards"})
    html = urllib.request.urlopen(request, timeout=20).read().decode("utf-8")

    # Each day is a <td data-date id> cell; its count is in the <tool-tip for=id> that labels it.
    dates = {m[1]: m[0] for m in re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"\s+id="([^"]+)"', html)}
    days = []
    for cell, label in re.findall(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        if cell not in dates:
            continue
        found = re.match(r"([\d,]+)\s+contribution", label.strip())
        days.append((dates[cell], int(found[1].replace(",", "")) if found else 0))
    if len(days) < 300:
        raise RuntimeError(f"only {len(days)} days found; the page layout may have changed")
    days.sort()

    OUT.write_text(json.dumps({"user": USER, "endDate": days[-1][0], "counts": [n for _, n in days]}) + "\n")
    print(f"github: {sum(n for _, n in days)} contributions over {len(days)} days, up to {days[-1][0]}")
except Exception as error:  # noqa: BLE001 - any failure keeps the saved calendar
    print(f"github: kept the saved calendar ({error})")
