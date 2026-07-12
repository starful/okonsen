#!/usr/bin/env python3
"""Recommended shrink plan for OKOnsen (GSC + cafe/seed removal)."""

from __future__ import annotations

import argparse
import csv
import io
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "app" / "content"
GUIDES = CONTENT / "guides"
GSC_ZIP = Path("/Users/starful/Downloads/okonsen.net-Performance-on-Search-2026-07-09.zip")
GSC_PAGES = ROOT / "tmp" / "gsc-export" / "페이지.csv"

CAFE_RE = re.compile(
    r"(cafe|coffee|latte|roast|kissaten|brew|espresso|drip|patisserie|blend_lab|phoenix_cafe)",
    re.I,
)
SEED_EXPAND = re.compile(r"^guide_(seed|expand)_\d+")

KEEP_GUIDES = frozenset(
    {
        "onsen_etiquette_basics",
        "onsen_etiquette_guide",
        "tattoo_friendly_onsen_list",
        "tattoo_friendly_master_list",
        "private_bath_kashikiri",
        "beppu_hell_tour_guide",
        "hakone_area_deep_dive",
        "hakone_day_trip_guide",
        "kurokawa_hidden_gems",
        "ryokan_kaiseki_experience",
        "ryokan_kaiseki_dining",
        "ryokan_vs_hotel",
        "kusatsu_onsen_guide",
        "onsen_manners",
        "japan_onsen_regions",
    }
)


def base_slug(stem: str) -> str:
    if stem.endswith("_en") or stem.endswith("_ko"):
        return stem.rsplit("_", 1)[0]
    return stem


def load_gsc() -> dict[tuple[str, str], dict[str, int]]:
    from collections import defaultdict

    agg: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"clicks": 0, "impressions": 0})
    pages_csv = GSC_PAGES
    if not pages_csv.exists() and GSC_ZIP.exists():
        with zipfile.ZipFile(GSC_ZIP) as z:
            for name in z.namelist():
                if name.endswith("페이지.csv") or "page" in name.lower():
                    raw = z.read(name).decode("utf-8-sig")
                    break
            else:
                return agg
    elif pages_csv.exists():
        raw = pages_csv.read_text(encoding="utf-8-sig")
    else:
        return agg

    for row in csv.DictReader(io.StringIO(raw)):
        url = (row.get("인기 페이지") or row.get("Top pages") or "").strip()
        clicks = int(row.get("클릭수") or row.get("Clicks") or 0)
        imp = int(row.get("노출") or row.get("Impressions") or 0)
        m = re.search(r"okonsen\.net/(onsen|guide)/([^/?#]+)", url)
        if not m:
            continue
        base = base_slug(m.group(2))
        agg[(m.group(1), base)]["clicks"] += clicks
        agg[(m.group(1), base)]["impressions"] += imp
    return agg


def stats(gsc: dict, kind: str, base: str) -> tuple[int, int]:
    d = gsc.get((kind, base), {"clicks": 0, "impressions": 0})
    return d["clicks"], d["impressions"]


def compute_lists(gsc: dict) -> tuple[list[str], list[str], list[str], list[str]]:
    onsen_bases = {base_slug(p.stem) for p in CONTENT.glob("*.md")}
    guide_bases = {base_slug(p.stem) for p in GUIDES.glob("*.md")}

    del_cafe = sorted(b for b in onsen_bases if CAFE_RE.search(b))
    del_seed = sorted(b for b in guide_bases if SEED_EXPAND.match(b))
    onsen = onsen_bases - set(del_cafe)
    guides = guide_bases - set(del_seed)

    del_onsen = sorted(b for b in onsen if stats(gsc, "onsen", b)[0] == 0 and stats(gsc, "onsen", b)[1] < 30)
    del_guides = sorted(
        b
        for b in guides
        if b not in KEEP_GUIDES and stats(gsc, "guide", b)[0] == 0 and stats(gsc, "guide", b)[1] <= 40
    )
    return del_cafe, del_seed, del_onsen, del_guides


def delete_topic(folder: Path, base: str, dry_run: bool) -> int:
    n = 0
    for lang in ("en", "ko"):
        path = folder / f"{base}_{lang}.md"
        if path.exists():
            if not dry_run:
                path.unlink()
            print(f"{'[dry] ' if dry_run else ''}🗑️  {path.relative_to(ROOT)}")
            n += 1
    return n


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.dry_run and not args.apply:
        parser.error("Pass --dry-run or --apply")

    gsc = load_gsc()
    del_cafe, del_seed, del_onsen, del_guides = compute_lists(gsc)
    print(
        f"Plan: cafe {len(del_cafe)} + seed {len(del_seed)} + onsen {len(del_onsen)} + guides {len(del_guides)} topics"
    )
    total = 0
    for b in del_cafe:
        total += delete_topic(CONTENT, b, args.dry_run)
    for b in del_onsen:
        total += delete_topic(CONTENT, b, args.dry_run)
    for b in del_seed:
        total += delete_topic(GUIDES, b, args.dry_run)
    for b in del_guides:
        total += delete_topic(GUIDES, b, args.dry_run)
    print(f"{'Would remove' if args.dry_run else 'Removed'} {total} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
