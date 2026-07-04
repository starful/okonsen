"""Onsen JSON cache and list helpers."""

from __future__ import annotations

import copy
import json
import os

try:
    from .config import CORE_ONSEN_IDS, DATA_FILE
    from .content_loader import prioritize_by_ids
    from .content_new import enrich_items
    from .images import thumbnail_with_v
except ImportError:
    from config import CORE_ONSEN_IDS, DATA_FILE
    from content_loader import prioritize_by_ids
    from content_new import enrich_items
    from images import thumbnail_with_v

CACHED_DATA = {"onsens": [], "last_updated": "2026.03.19"}
_CACHE_MTIME: float = 0.0


def ensure_onsen_cache() -> None:
    global CACHED_DATA, _CACHE_MTIME
    if not os.path.exists(DATA_FILE):
        return
    try:
        mtime = os.path.getmtime(DATA_FILE)
    except OSError:
        return
    if mtime <= _CACHE_MTIME:
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            CACHED_DATA = json.load(f)
        _CACHE_MTIME = mtime
        print(f"✅ 온천 데이터 로드 완료: {len(CACHED_DATA.get('onsens', []))}개")
    except Exception as e:
        print(f"❌ 데이터 로드 오류: {e}")


def public_onsen(row: dict) -> dict:
    out = copy.deepcopy(row)
    out["thumbnail"] = thumbnail_with_v(
        out.get("thumbnail", ""), out.get("published")
    )
    return out


def get_footer_stats(lang: str) -> dict:
    """모든 페이지에서 풋터 수치가 0이 되지 않도록 실시간 계산"""
    data_list = CACHED_DATA.get("onsens", [])
    filtered_count = len([o for o in data_list if o.get("lang") == lang])
    return {
        "total_onsens": filtered_count if filtered_count > 0 else len(data_list) // 2,
        "last_updated": CACHED_DATA.get("last_updated", "2026.03.19"),
    }


def get_featured_onsens(lang: str, limit: int = 12) -> list:
    """서버사이드 내부 링크용 온천 목록(크롤러가 바로 따라갈 수 있는 링크)"""
    ensure_onsen_cache()
    data_list = CACHED_DATA.get("onsens", [])
    filtered = [o for o in data_list if o.get("lang") == lang]
    if not filtered:
        filtered = [o for o in data_list if o.get("lang") == "en"]
    lang_ids = [oid for oid in CORE_ONSEN_IDS if oid.endswith(f"_{lang}")]
    ranked = prioritize_by_ids(filtered, lang_ids)
    return enrich_items(ranked[:limit])


ensure_onsen_cache()
