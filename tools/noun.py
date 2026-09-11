#!/usr/bin/env python3
"""Fetch Noun Project icons for the pattern pages (search → pick → download SVG in brand purple).

    python3 tools/noun.py search "plug"                # list candidates (id, term, creator)
    python3 tools/noun.py get 1234567 what-agent       # download as icons/what-agent.svg + append attribution

Uses NOUN_PROJECT_API_KEY / NOUN_PROJECT_API_SECRET from ~/.env (OAuth 1.0a).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

HERE = Path(__file__).resolve().parent.parent
ICONS = HERE / "icons"
ATTRIB = ICONS / "ATTRIBUTION.txt"
COLOR = "6430AB"  # matches the existing t1–t5 icons
BASE = "https://api.thenounproject.com/v2"


def creds() -> OAuth1:
    env = {}
    for line in (Path.home() / ".env").read_text().splitlines():
        if line.startswith("NOUN_PROJECT_API_KEY=") or line.startswith("NOUN_PROJECT_API_SECRET="):
            k, v = line.split("=", 1)
            env[k] = v.strip().strip('"')
    return OAuth1(env["NOUN_PROJECT_API_KEY"], env["NOUN_PROJECT_API_SECRET"])


def search(term: str, limit: int = 8) -> None:
    r = requests.get(f"{BASE}/icon", params={"query": term, "limit": limit, "thumbnail_size": 84}, auth=creds(), timeout=30)
    r.raise_for_status()
    for icon in r.json().get("icons", []):
        print(f"{icon['id']:>9}  {icon.get('term','')!s:<28} by {icon.get('creator',{}).get('name','?')}  {icon.get('thumbnail_url','')}")


def get(icon_id: str, name: str) -> None:
    auth = creds()
    meta = requests.get(f"{BASE}/icon/{icon_id}", auth=auth, timeout=30)
    meta.raise_for_status()
    icon = meta.json()["icon"]
    dl = requests.get(f"{BASE}/icon/{icon_id}/download", params={"color": COLOR, "filetype": "svg"}, auth=auth, timeout=60)
    dl.raise_for_status()
    body = dl.json()
    svg = requests.get(body["base64_encoded_file"] if body.get("base64_encoded_file", "").startswith("http") else body["url"], timeout=60).text if body.get("url") else None
    if svg is None:
        import base64
        svg = base64.b64decode(body["base64_encoded_file"]).decode("utf-8")
    svg = re.sub(r"<text[^>]*>.*?</text>", "", svg, flags=re.S)  # strip any embedded attribution text
    out = ICONS / f"{name}.svg"
    out.write_text(svg)
    line = f'"{icon.get("term","")}" by {icon.get("creator",{}).get("name","?")} (Noun Project, id {icon_id})\n'
    if line not in ATTRIB.read_text():
        ATTRIB.open("a").write(line)
    print(f"saved {out.relative_to(HERE)} · {line.strip()}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "search":
        search(" ".join(sys.argv[2:]))
    elif len(sys.argv) == 4 and sys.argv[1] == "get":
        get(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
