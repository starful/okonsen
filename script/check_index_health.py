#!/usr/bin/env python3
"""Indexing health monitor for okonsen.net (GSC "미색인" 진단).

Two passes:
1. Local (default) — rescans app/content for thin/duplicate bodies using the
   same gate as sitemap generation (see app/seo.dedupe_longtail) and flags any
   that are still listed in the committed sitemap files, so a stale sitemap
   doesn't keep advertising pages GSC will never index.
2. Live (--live) — fetches a sample of sitemap URLs over HTTP and checks for
   robots-meta / canonical mistakes that silently block indexing.

Usage:
    python script/check_index_health.py
    python script/check_index_health.py --live --limit 40
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import frontmatter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from seo import SEO_REDIRECTS, dedupe_longtail  # noqa: E402

CONTENT_DIR = ROOT / "app" / "content"
GUIDE_DIR = CONTENT_DIR / "guides"
STATIC_DIR = ROOT / "app" / "static"
SITEMAP_FILES = ["sitemap-core.xml", "sitemap-longtail.xml"]

sys.path.insert(0, str(ROOT / "script"))
from build_data import body_fingerprint, normalize_markdown_source  # noqa: E402


def sitemap_urls() -> set[str]:
    urls: set[str] = set()
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    for name in SITEMAP_FILES:
        path = STATIC_DIR / name
        if not path.exists():
            continue
        tree = ET.parse(path)
        for loc in tree.getroot().iter(f"{ns}loc"):
            if loc.text:
                urls.add(loc.text.strip())
    return urls


def collect_local(prefix: str, content_dir: Path) -> list[dict]:
    items = []
    if not content_dir.exists():
        return items
    for path in sorted(content_dir.glob("*.md")):
        link = f"/{prefix}/{path.stem}"
        if link in SEO_REDIRECTS:
            continue
        try:
            post = frontmatter.loads(normalize_markdown_source(path.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"❌ 파일 처리 오류 ({path.name}): {e}")
            continue
        body_chars, body_hash = body_fingerprint(post.content)
        items.append({"id": path.stem, "link": link, "body_chars": body_chars, "body_hash": body_hash})
    return items


def local_report() -> int:
    onsens = collect_local("onsen", CONTENT_DIR)
    guides = collect_local("guide", GUIDE_DIR)
    kept_onsens = dedupe_longtail(onsens, kind="onsen")
    kept_guides = dedupe_longtail(guides, kind="guide")
    flagged = [i for i in onsens if i not in kept_onsens] + [i for i in guides if i not in kept_guides]

    print(f"🔎 로컬 점검: 온천 {len(onsens)}개 / 가이드 {len(guides)}개")
    print(f"   - thin/duplicate로 걸러진 항목: {len(flagged)}개")

    live_urls = sitemap_urls()
    stale = [i for i in flagged if f"https://okonsen.net{i['link']}" in live_urls]
    if stale:
        print(f"⚠️  사이트맵에 아직 남아있는 thin/duplicate URL {len(stale)}개 (build_data.py 재실행 필요):")
        for i in stale[:20]:
            print(f"     - {i['link']}")
    else:
        print("✅  사이트맵은 thin/duplicate 항목을 광고하지 않음")
    return len(stale)


def live_report(limit: int) -> int:
    import requests
    from bs4 import BeautifulSoup

    urls = sorted(sitemap_urls())[:limit]
    print(f"🌐 라이브 점검: {len(urls)}개 URL (limit={limit})")
    problems = 0
    for url in urls:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "okonsen-index-health/1.0"})
        except requests.RequestException as e:
            print(f"   ❌ {url} — 요청 실패: {e}")
            problems += 1
            continue
        if resp.status_code != 200:
            print(f"   ❌ {url} — status {resp.status_code}")
            problems += 1
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        robots_tag = soup.find("meta", attrs={"name": "robots"})
        robots_content = (robots_tag.get("content") or "").lower() if robots_tag else ""
        if "noindex" in robots_content:
            print(f"   ❌ {url} — robots meta noindex")
            problems += 1

        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        canonical_href = (canonical_tag.get("href") or "").strip() if canonical_tag else ""
        if not canonical_href:
            print(f"   ⚠️  {url} — canonical 태그 없음")
            problems += 1
        elif canonical_href.rstrip("/") != url.rstrip("/"):
            print(f"   ⚠️  {url} — canonical 불일치: {canonical_href}")
            problems += 1

    if not problems:
        print("✅  robots meta / canonical 오류 없음")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="HTTP로 sitemap URL의 robots/canonical 점검")
    parser.add_argument("--limit", type=int, default=30, help="--live 사용 시 점검할 URL 수")
    args = parser.parse_args()

    issues = local_report()
    if args.live:
        issues += live_report(args.limit)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
