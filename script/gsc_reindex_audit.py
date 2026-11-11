#!/usr/bin/env python3
"""GSC 미색인 진단 + 우선순위 재제출 큐 생성기 (okonsen.net).

Search Console → 색인 → 페이지 보고서에서 "미색인" 이유별로 내보낸 CSV
(URL 컬럼 포함)를 sitemap-core.xml / sitemap-longtail.xml과 대조해 분류한다:

1. 이미 사이트맵에서 제외됨 — thin/duplicate 필터가 이미 처리함 (조치 불필요)
2. 사이트맵에 남아있지만 thin/duplicate — canonical 통합 대상 (dedupe_longtail 재확인 필요)
3. 사이트맵에 남아있고 콘텐츠는 정상 — 재색인 요청 대상

Search Console의 URL 검사 도구는 색인 요청을 공개 API로 제공하지 않고(일일
수동 할당량), 한 번에 한 URL만 처리할 수 있다. 이 스크립트는 실제 제출을
대신하지 않고, 제출 순서 큐를 만들어 담당자가 URL 검사 도구에서 순서대로
처리할 수 있게 한다.

--gsc-performance-csv로 Search Console 실적 보고서(페이지별 클릭/노출수)
CSV를 함께 넘기면 조회수가 높았던 페이지(한때 색인되어 트래픽이 있었으나
지금은 미색인인 페이지)부터 우선 재제출하도록 큐를 정렬한다. 생략하면
seo_priority의 고정 우선순위 목록으로 대체한다.

Usage:
    python script/gsc_reindex_audit.py --gsc-csv not_indexed_export.csv
    python script/gsc_reindex_audit.py --gsc-csv not_indexed_export.csv --limit 15 --out queue.txt
    python script/gsc_reindex_audit.py --gsc-csv not_indexed_export.csv \
        --gsc-performance-csv performance_export.csv
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

from seo import SEO_REDIRECTS, dedupe_longtail  # noqa: E402
from seo_priority import CORE_GUIDE_BASES, CORE_ONSEN_IDS, guide_id  # noqa: E402
from build_data import body_fingerprint, normalize_markdown_source  # noqa: E402

CONTENT_DIR = ROOT / "app" / "content"
GUIDE_DIR = CONTENT_DIR / "guides"
STATIC_DIR = ROOT / "app" / "static"
SITEMAP_FILES = ["sitemap-core.xml", "sitemap-longtail.xml"]
BASE_URL = "https://okonsen.net"


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


def thin_duplicate_links() -> set[str]:
    """Links (e.g. '/onsen/foo_en') that the sitemap generator would drop as thin/duplicate."""
    flagged: set[str] = set()
    for prefix, content_dir, kind in (("onsen", CONTENT_DIR, "onsen"), ("guide", GUIDE_DIR, "guide")):
        if not content_dir.exists():
            continue
        items = []
        for path in sorted(content_dir.glob("*.md")):
            link = f"/{prefix}/{path.stem}"
            if link in SEO_REDIRECTS:
                continue
            try:
                post = frontmatter.loads(normalize_markdown_source(path.read_text(encoding="utf-8")))
            except Exception:
                continue
            body_chars, body_hash = body_fingerprint(post.content)
            items.append({"id": path.stem, "link": link, "body_chars": body_chars, "body_hash": body_hash})
        kept_links = {i["link"] for i in dedupe_longtail(items, kind=kind)}
        flagged |= {i["link"] for i in items if i["link"] not in kept_links}
    return flagged


def load_gsc_not_indexed(csv_path: Path) -> set[str]:
    """Parse a GSC Indexing-report drilldown CSV export (URL column, header name varies)."""
    urls: set[str] = set()
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows:
        return urls
    header = rows[0]
    has_header = any("url" in cell.strip().lower() for cell in header)
    url_col = 0
    if has_header:
        for idx, cell in enumerate(header):
            if "url" in cell.strip().lower():
                url_col = idx
                break
    data_rows = rows[1:] if has_header else rows
    for row in data_rows:
        if url_col >= len(row):
            continue
        value = row[url_col].strip()
        if value.startswith(BASE_URL):
            urls.add(value)
    return urls


def load_gsc_performance(csv_path: Path) -> dict[str, int]:
    """Parse a GSC Performance-report CSV export (Page/URL column + Clicks or Impressions)."""
    metrics: dict[str, int] = {}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows:
        return metrics
    header = rows[0]
    url_col = next(
        (i for i, cell in enumerate(header) if "url" in cell.strip().lower() or "page" in cell.strip().lower()), 0
    )
    metric_col = next((i for i, cell in enumerate(header) if "click" in cell.strip().lower()), None)
    if metric_col is None:
        metric_col = next((i for i, cell in enumerate(header) if "impression" in cell.strip().lower()), None)
    if metric_col is None:
        return metrics
    for row in rows[1:]:
        if url_col >= len(row) or metric_col >= len(row):
            continue
        url = row[url_col].strip()
        if not url.startswith(BASE_URL):
            continue
        try:
            metrics[url] = int(float(row[metric_col].replace(",", "").strip() or 0))
        except ValueError:
            continue
    return metrics


def priority_order() -> list[str]:
    """Flattened priority URLs, highest priority first (mirrors seo_priority sets)."""
    order = [f"{BASE_URL}/onsen/{oid}" for oid in CORE_ONSEN_IDS]
    for base in CORE_GUIDE_BASES:
        order.append(f"{BASE_URL}/guide/{guide_id(base, 'en')}")
        order.append(f"{BASE_URL}/guide/{guide_id(base, 'ko')}")
    return order


def build_queue(
    not_indexed: set[str],
    sitemap: set[str],
    thin_links: set[str],
    limit: int,
    performance: dict[str, int] | None = None,
) -> list[str]:
    actionable = {
        u for u in not_indexed
        if u in sitemap and u[len(BASE_URL):] not in thin_links
    }
    if performance:
        priority_rank = {u: idx for idx, u in enumerate(priority_order())}
        queue = sorted(actionable, key=lambda u: (-performance.get(u, 0), priority_rank.get(u, 999), u))
    else:
        ranked = [u for u in priority_order() if u in actionable]
        remaining = sorted(actionable - set(ranked))
        queue = ranked + remaining
    return queue[:limit] if limit else queue


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gsc-csv", required=True, type=Path, help="GSC 색인 보고서 '미색인' 드릴다운 CSV 경로")
    parser.add_argument(
        "--gsc-performance-csv", type=Path,
        help="GSC 실적 보고서(페이지별 클릭/노출수) CSV 경로. 지정 시 조회수 높은 순으로 큐를 정렬",
    )
    parser.add_argument(
        "--limit", type=int, default=15,
        help="재제출 큐에 담을 최대 URL 수 (URL 검사 도구는 1건씩 수동 제출, 일일 할당량 제한). 0=무제한",
    )
    parser.add_argument("--out", type=Path, help="큐를 줄바꿈 텍스트로 저장할 경로 (생략 시 콘솔 출력만)")
    args = parser.parse_args()

    if not args.gsc_csv.exists():
        print(f"❌ CSV 파일을 찾을 수 없습니다: {args.gsc_csv}")
        return 1

    not_indexed = load_gsc_not_indexed(args.gsc_csv)
    if not not_indexed:
        print(f"⚠️  CSV에서 okonsen.net URL을 찾지 못했습니다: {args.gsc_csv}")
        return 1

    performance: dict[str, int] = {}
    if args.gsc_performance_csv:
        if not args.gsc_performance_csv.exists():
            print(f"❌ 실적 보고서 CSV 파일을 찾을 수 없습니다: {args.gsc_performance_csv}")
            return 1
        performance = load_gsc_performance(args.gsc_performance_csv)
        if performance:
            print(f"📈 실적 보고서: {len(performance)}개 URL의 조회수 데이터 로드")
        else:
            print(f"⚠️  실적 보고서 CSV에서 조회수 컬럼을 찾지 못했습니다: {args.gsc_performance_csv}")

    sitemap = sitemap_urls()
    thin_links = thin_duplicate_links()

    still_advertised = not_indexed & sitemap
    already_dropped = not_indexed - sitemap
    thin_in_sitemap = {u for u in still_advertised if u[len(BASE_URL):] in thin_links}

    print(f"📄 GSC 미색인 URL: {len(not_indexed)}개")
    print(f"   - 이미 사이트맵에서 제외됨 (조치 불필요): {len(already_dropped)}개")
    print(f"   - 사이트맵에 남아있음: {len(still_advertised)}개")
    if thin_in_sitemap:
        print(f"     └ thin/duplicate — canonical 통합 필요: {len(thin_in_sitemap)}개")
        for u in sorted(thin_in_sitemap)[:20]:
            print(f"        - {u}")

    queue = build_queue(not_indexed, sitemap, thin_links, args.limit, performance=performance)
    order_desc = "조회수 높은 순" if performance else "seo_priority 고정 순위"
    print(f"\n🚀 URL 검사 도구 재제출 큐 ({order_desc}, {len(queue)}개, limit={args.limit or '무제한'}):")
    for u in queue:
        hits = performance.get(u) if performance else None
        print(f"   - {u}" + (f" (조회수 {hits})" if hits else ""))

    if args.out:
        args.out.write_text("\n".join(queue) + ("\n" if queue else ""), encoding="utf-8")
        print(f"\n💾 큐 저장: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
