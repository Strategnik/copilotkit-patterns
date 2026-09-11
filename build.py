#!/usr/bin/env python3
"""Build the CopilotKit Patterns campaign pages from patterns.json + the two templates.

    python3 build.py --out <dir> [--base /patterns] [--asset ../]

Emits <out>/index.html (gallery) and <out>/<slug>/index.html for each pattern, plus the
logo + icon assets. Two layouts are supported through --base/--asset:

  * Site build (default): --base /patterns  --asset ../
      Files land in the website repo under public/campaign-pages/patterns/. Each page is
      iframed by a Next route at /patterns/<slug>, so in-page navigation uses target=_top
      and absolute pretty URLs (/patterns/<slug>), while assets resolve relative to the
      iframe document (../logo-full.svg → /campaign-pages/patterns/logo-full.svg).

  * Standalone preview: --base "" --asset ../
      Same files served from any static host root (Vercel preview). Pretty URLs become
      /<slug>, and there is no parent frame, so bridge events are simply not sent.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCENES = {
    "sc1": '<i class="grid"></i><i class="draw"></i><i class="cur"></i><i class="note"></i>',
    "sc2": '<i class="b b1"></i><i class="b b2"></i><i class="b b3"></i><i class="bar"></i><i class="bar bar2"></i>',
    "sc3": '<i class="lk lk1"></i><i class="lk lk2"></i><i class="nd n1"></i><i class="nd n2"></i><i class="nd n3"></i><i class="pl"></i>',
    "sc4": '<i class="bub ba"><i class="dt"></i><i class="dt"></i><i class="dt"></i></i><i class="bub bb"></i>',
    "sc5": '<i class="bar"></i><i class="st s1"></i><i class="st s2"></i><i class="st s3"></i>',
}
KEYWORDS = r"\b(import|from|const|new|return|await|async|export|default|function)\b"


def highlight(code: str) -> str:
    """Tiny, dependency-free highlighter: comments, strings, keywords, call names."""
    out: list[str] = []
    for line in code.split("\n"):
        # split off a trailing // comment (not inside a string — good enough for these snippets)
        m = re.search(r"(^|\s)//.*$", line)
        comment = ""
        if m and line.count('"') % 2 == 0:
            comment, line = line[m.start() :], line[: m.start()]
        esc = html.escape(line)
        esc = re.sub(r'(&quot;[^&]*?&quot;)', r'<span class="s">\1</span>', esc)
        esc = re.sub(KEYWORDS, r'<span class="k">\1</span>', esc)
        esc = re.sub(r"\b(use[A-Z]\w*|createChannel|required)(?=\()", r'<span class="f">\1</span>', esc)
        if comment:
            esc += f'<span class="c">{html.escape(comment)}</span>'
        out.append(esc)
    return "\n".join(out)


def render(template: str, ctx: dict[str, str]) -> str:
    def sub(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in ctx:
            raise KeyError(f"template variable {{{{{key}}}}} has no value")
        return ctx[key]

    return re.sub(r"\{\{(\w+)\}\}", sub, template)


def pretty(base: str, slug: str | None) -> str:
    return f"{base}/{slug}" if slug else f"{base}/"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default="/patterns", help="URL prefix of the pretty routes ('' for preview)")
    ap.add_argument("--asset", default="../", help="relative path from a pattern page to the asset folder")
    args = ap.parse_args()

    data = json.loads((HERE / "patterns.json").read_text())
    tpl = (HERE / "template.html").read_text()
    idx_tpl = (HERE / "index-template.html").read_text()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = args.base.rstrip("/")

    # assets
    for name in ("logo-full.svg", "logo-mark.svg"):
        shutil.copy(HERE / name, out / name)
    (out / "icons").mkdir(exist_ok=True)
    for icon in (HERE / "icons").iterdir():
        shutil.copy(icon, out / "icons" / icon.name)

    patterns = data["patterns"]
    score = data["scorecard"]

    def tile(p: dict, asset: str, compact: bool) -> str:
        tag = "h3" if compact else "h2"
        return (
            f'<a class="tile" href="{pretty(base, p["slug"])}" target="_top" data-to="{p["slug"]}">'
            f'<span class="idx" aria-hidden="true">{p["idx"]}</span>'
            f'<img src="{asset}icons/{p["icon"]}.svg" alt="">'
            f'<span class="t"><{tag}>{html.escape(p["card_title"])}</{tag}><p>{html.escape(p["card_desc"])}</p></span>'
            f'<span class="arrow" aria-hidden="true">→</span></a>'
        )

    def score_tile(compact: bool) -> str:
        tag = "h3" if compact else "h2"
        return (
            f'<a class="tile score" href="{data["scorecard_url"]}" target="_top" data-cta="scorecard">'
            f'<span class="idx" aria-hidden="true">{score["idx"]}</span>'
            f'<span class="sc" aria-hidden="true">/14</span>'
            f'<span class="t"><{tag}>{html.escape(score["card_title"])}</{tag}><p>{html.escape(score["card_desc"])}</p></span>'
            f'<span class="arrow" aria-hidden="true">→</span></a>'
        )

    # gallery
    tiles = "".join(tile(p, "", False) for p in patterns) + score_tile(False)
    (out / "index.html").write_text(
        render(idx_tpl, {"asset": "", "tiles_html": tiles, "engineer_url": data["engineer_url"]})
    )

    # pattern pages
    for p in patterns:
        others = [q for q in patterns if q["slug"] != p["slug"]]
        strip = "".join(tile(q, args.asset, True) for q in others) + score_tile(True)
        steps = "".join(
            f'<div class="step"><div class="n">{i + 1:02d}</div><h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></div>'
            for i, (t, d) in enumerate(p["steps"])
        )
        ctx = {
            "slug": p["slug"],
            "use_case": p["use_case"],
            "idx": p["idx"],
            "nav_title_lc": p["nav_title"].lower(),
            "h1_pre": html.escape(p["h1_pre"]),
            "h1_accent": html.escape(p["h1_accent"]),
            "h1_post": html.escape(p["h1_post"]),
            "sub": html.escape(p["sub"]),
            "demo_url": p["demo_url"],
            "demo_label": html.escape(p["demo_label"]),
            "guide_url": p["guide_url"],
            "guide_label": html.escape(p["guide_label"]),
            "code_file": html.escape(p["code_file"]),
            "code_html": highlight(p["code"]),
            "install": html.escape(data["install"]),
            "steps_html": steps,
            "strip_html": strip,
            "scene": p["scene"],
            "scene_html": SCENES[p["scene"]],
            "scorecard_url": data["scorecard_url"],
            "engineer_url": data["engineer_url"],
            "meta_title": html.escape(p["meta_title"]),
            "meta_desc": html.escape(p["meta_desc"]),
            "asset": args.asset,
            "base": base,
        }
        d = out / p["slug"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(render(tpl, ctx))
        print(f"  {d / 'index.html'}")
    print(f"  {out / 'index.html'}")


if __name__ == "__main__":
    main()
