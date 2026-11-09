#!/usr/bin/env python3
"""okonsen.net 미색인 원인 분류 배치 (app/seo.py 규칙 기반, 사이트맵 생성은 build_data.py).

app/content 전체를 스캔해 각 페이지를 아래 사유 중 하나로 분류한다:
  - thin            : 본문이 THIN_CONTENT_MIN_CHARS 미만 (얇은 콘텐츠)
  - duplicate       : 동일 본문 해시를 가진 선행 페이지가 이미 있음 (중복 콘텐츠)
  - missing_sitemap : thin/duplicate는 아니지만 sitemap-core/longtail.xml에 없음 (노출 누락)
  - ok              : 위 사유 없음 + 사이트맵에도 있음 (정상 색인 대상)

SEO_REDIRECTS(301 대상)로 이미 영구 제외된 경로는 이름이 끊긴 콘텐츠이므로
집계에서 빼고 건수만 참고용으로 보여준다.

Usage:
    python script/index_status_report.py
    python script/index_status_report.py --out script/reports/index_status.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import frontmatter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "script"))

from seo import SEO_REDIRECTS, flag_unindexable_reason  # noqa: E402
from build_data import body_fingerprint, normalize_markdown_source  # noqa: E402

CONTENT_DIR = ROOT / "app" / "content"
GUIDE_DIR = CONTENT_DIR / "guides"
STATIC_DIR = ROOT / "app" / "static"
SITEMAP_FILES = ["sitemap-core.xml", "sitemap-longtail.xml"]
BASE_URL = "https://okonsen.net"

REASON_ORDER = ("thin", "duplicate", "missing_sitemap", "ok")


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


def collect(prefix: str, content_dir: Path) -> list[dict]:
    """Links still carrying content, newest/id-sorted (skips SEO_REDIRECTS sources)."""
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


def classify(items: list[dict], *, kind: str, sitemap: set[str]) -> list[dict]:
    seen_hashes: set[str] = set()
    rows = []
    for item in items:
        reason = flag_unindexable_reason(item, kind=kind, seen_hashes=seen_hashes)
        if reason is None:
            reason = "ok" if f"{BASE_URL}{item['link']}" in sitemap else "missing_sitemap"
        rows.append({**item, "kind": kind, "reason": reason})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, help="전체 결과를 CSV로 저장할 경로")
    args = parser.parse_args()

    sitemap = sitemap_urls()
    rows = (
        classify(collect("onsen", CONTENT_DIR), kind="onsen", sitemap=sitemap)
        + classify(collect("guide", GUIDE_DIR), kind="guide", sitemap=sitemap)
    )

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["reason"]] = counts.get(row["reason"], 0) + 1

    print(f"🔎 전체 콘텐츠 {len(rows)}개 점검 (redirect로 이미 제외된 경로 {len(SEO_REDIRECTS)}개는 집계 제외)")
    for reason in REASON_ORDER:
        if counts.get(reason):
            print(f"   - {reason}: {counts[reason]}개")

    flagged = [r for r in rows if r["reason"] != "ok"]
    if flagged:
        print(f"\n⚠️  색인 방해 요인이 있는 페이지 {len(flagged)}개:")
        for r in flagged[:30]:
            print(f"     - [{r['reason']}] {r['link']}")
    else:
        print("\n✅  thin/duplicate/missing_sitemap 없음")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["link", "kind", "reason", "body_chars", "body_hash"])
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r[k] for k in writer.fieldnames})
        print(f"\n💾 전체 결과 저장: {args.out}")

    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
