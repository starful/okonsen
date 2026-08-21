import os
import csv
import sys
from datetime import datetime
from dotenv import load_dotenv
import concurrent.futures

from topic_queue_csv import resolve as resolve_queue_csv
from content_guards import (
    locale_pair_status,
    sibling_exists,
    strip_code_fences,
    validate_generated_markdown,
)
from content_quality import is_off_onsen_theme


def _emit_pipeline_result(**kwargs):
    try:
        from generation_result import emit_generation_result

        emit_generation_result(**kwargs)
    except ImportError:
        pass

# ==========================================
# ⚙️ 설정 (GCS 경로 및 환경 설정)
# ==========================================
load_dotenv()

def _claude_md(prompt: str) -> str:
    """MD text via Claude CLI subscription (not Claude API)."""
    import sys
    from pathlib import Path
    _shared = Path(__file__).resolve().parents[2] / "_shared"
    if str(_shared) not in sys.path:
        sys.path.insert(0, str(_shared))
    from site_llm import generate_md_text
    return generate_md_text(prompt)

# GEMINI_API_KEY no longer required for MD (Claude CLI)
GCS_IMAGE_BASE = "https://storage.googleapis.com/ok-project-assets/okonsen"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')

TARGET_LANGS = ['en', 'ko']
CATEGORIES = {
    "en": ["Private Bath", "Tattoo OK", "Great View", "Luxury", "Local"],
    "ko": ["가족탕", "타투 허용", "절경", "고급 료칸", "로컬"]
}

def generate_onsen_md(safe_name, name, lat, lng, address, lang, features):
    """Claude 2.0을 사용한 고퀄리티 컨텐츠 생성 (8000자 지향 및 폰트 크기 최적화)"""
    pass  # Claude CLI; API_KEY unused
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    allowed_categories = ", ".join(CATEGORIES.get(lang, CATEGORIES["en"]))
    thumbnail_url = f"{GCS_IMAGE_BASE}/{safe_name}.jpg"
    filling_sibling = sibling_exists(CONTENT_DIR, safe_name, lang)
    length_hint = (
        "9,000+ characters — this fills a missing locale beside an existing page; "
        "match or exceed the sibling's depth."
        if filling_sibling
        else "7,000 to 8,000 characters"
    )

    # 💡 [프롬프트 수정] 제목 태그 제한 및 본문 스타일 지침 추가
    prompt = f"""
    You are an elite travel journalist specializing in Japanese Onsens.
    Write an EXTREMELY comprehensive, deeply detailed guide for '{name}' located at {address}.
    Target Language: {lang}
    Aim for a very long response, around {length_hint}.
    Write ONLY in {"Korean" if lang == "ko" else "English"}; do not mix languages.

    [Formatting Rules - CRITICAL]
    1. NEVER use the '#' (H1) tag inside the body content.
    2. Use '##' for main sections (History, Baths, etc.).
    3. Use '###' for subsections.
    4. DO NOT wrap an entire paragraph in bold (****). Only bold specific keywords or short phrases.
    5. DO NOT use heading tags for normal sentences.

    Structure (cover these themes with UNIQUE ## titles for THIS ryokan —
    do not copy identical section labels across every property):
    - Introduction (vibe, first impression, and why it's unique)
    - History & Tradition (of the ryokan or the town)
    - Deep Dive into the Baths (Water quality, minerals, and the exact view)
    - Rooms & Architecture (Wabi-sabi aesthetics and comfort)
    - Gastronomy (Detailed description of the Kaiseki dinner and breakfast)
    - Local Attractions (What to do around {address})
    - Practical Tips (Tattoo policy, best season, and booking hacks)
    - Access Guide (How to get there)

    Output MUST be in this YAML format:
    ---
    lang: {lang}
    title: "Write a catchy SEO title here"
    lat: {lat}
    lng: {lng}
    categories: ["Category 1", "Category 2"]
    thumbnail: "{thumbnail_url}"
    address: "{address}"
    date: "{current_date}"
    summary: "3-sentence engaging summary"
    ---
    (Body content in Markdown following the formatting rules above)
    """

    try:
        response_text = _claude_md(prompt)
        content = strip_code_fences(response_text or "")

        ok, errors = validate_generated_markdown(
            content,
            kind="onsen",
            lang=lang,
            sibling_exists=filling_sibling,
        )
        if not ok:
            print(f"⛔ [품질미달·저장안함] {safe_name}_{lang}.md — {', '.join(errors)}")
            return False

        filepath = os.path.join(CONTENT_DIR, f"{safe_name}_{lang}.md")
        os.makedirs(CONTENT_DIR, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ [완료] {safe_name}_{lang}.md (약 {len(content)}자)")
        return True
    except Exception as e:
        print(f"❌ [에러] {name}: {e}")
        return False

def process_csv_auto(limit=10):
    csv_path = resolve_queue_csv("items", os.path.join(SCRIPT_DIR, "csv", "onsens.csv"))
    if not os.path.exists(csv_path):
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_path}")
        return

    tasks = []
    pairs_queued = 0
    half_skipped = 0
    with open(csv_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if limit > 0 and pairs_queued >= limit:
                break
            name = row.get('Name', '').strip()
            if not name:
                continue

            safe_name = name.lower().replace(" ", "_").replace("'", "").replace(",", "")
            features = (row.get("Features") or "").strip()
            address = (row.get("Address") or "").strip()
            if is_off_onsen_theme(safe_name, name, features=features, address=address):
                print(f"⏭️  Skip off-theme CSV row: {name} ({safe_name})")
                continue
            status = locale_pair_status(CONTENT_DIR, safe_name)
            if status == "complete":
                continue
            fill_half = os.environ.get("FILL_HALF", "").strip().lower() in ("1", "true", "yes")
            if fill_half:
                if status != "half":
                    continue
                for lang in TARGET_LANGS:
                    if not os.path.isfile(os.path.join(CONTENT_DIR, f"{safe_name}_{lang}.md")):
                        tasks.append(
                            (safe_name, name, row['Lat'], row['Lng'], row['Address'], lang, row['Features'])
                        )
                pairs_queued += 1
                continue
            if status == "half":
                half_skipped += 1
                continue

            # New pair only: always queue en+ko together.
            for lang in TARGET_LANGS:
                tasks.append(
                    (safe_name, name, row['Lat'], row['Lng'], row['Address'], lang, row['Features'])
                )
            pairs_queued += 1

    if half_skipped:
        print(f"⏭️  반쪽(en/ko 한쪽만) {half_skipped}건 — 신규 페어 우선으로 스킵")

    if tasks:
        print(f"⚡️ {pairs_queued}페어 · {len(tasks)}파일 신규 생성 시작...")
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda p: generate_onsen_md(*p), tasks))
        ok = sum(1 for r in results if r)
        _emit_pipeline_result(
            step="items",
            topics=pairs_queued,
            generated=ok,
            failed=len(tasks) - ok,
            skipped=half_skipped,
        )
    else:
        print("💡 새로 생성할 컨텐츠가 없습니다.")
        _emit_pipeline_result(step="items", topics=0, generated=0, skipped=half_skipped)

if __name__ == "__main__":
    # 기본 10개 주제, 인자/환경변수로 오버라이드 가능
    env_limit = os.environ.get("CONTENT_LIMIT")
    arg_limit = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        run_limit = int(arg_limit or env_limit or 10)
    except ValueError:
        run_limit = 10
    process_csv_auto(limit=run_limit)
