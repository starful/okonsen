import os
import csv
import sys
import concurrent.futures
from datetime import datetime
from google import genai
from dotenv import load_dotenv

from topic_queue_csv import resolve as resolve_queue_csv
from content_guards import (
    duplicate_guide_reason,
    sibling_exists,
    strip_code_fences,
    validate_generated_markdown,
)


def _emit_pipeline_result(**kwargs):
    try:
        from generation_result import emit_generation_result

        emit_generation_result(**kwargs)
    except ImportError:
        pass

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

DEFAULT_GUIDE_CSV = "script/csv/guides.csv"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "content", "guides")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _guides_csv_path() -> str:
    return resolve_queue_csv("guides", DEFAULT_GUIDE_CSV)


def generate_guide(row, lang):
    base_id = (row.get('id') or '').strip()
    if not base_id:
        return "❌ 에러: id 없음"

    dup = duplicate_guide_reason(base_id, OUTPUT_DIR)
    if dup:
        return f"⏭️ 스킵(중복주제): {base_id}_{lang} — {dup}"

    topic = row.get(f'topic_{lang}') or ''
    keywords = row.get('keywords') or ''
    filename = f"{base_id}_{lang}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    filling_sibling = sibling_exists(OUTPUT_DIR, base_id, lang)
    length_hint = (
        "at least 6,500 characters — filling a missing locale; match sibling depth"
        if filling_sibling
        else "at least 5,000 characters"
    )

    # 본문 생성 프롬프트
    prompt = f"""
    Write an exhaustive, professional SEO travel guide about '{topic}' in Japan.
    Target Language: {lang}
    Keywords to include: {keywords}
    Length: {length_hint}.
    Write ONLY in {"Korean" if lang == "ko" else "English"}; do not mix languages.

    Structure:
    1. Deep introduction.
    2. Historical context or cultural significance.
    3. Practical 'How-to' or 'Where-to' tips.
    4. Expert recommendations.
    5. Conclusion.

    Use '##' for main sections (at least 4 sections). Never use H1 ('#').
    Invent UNIQUE ## titles for THIS topic — do not reuse interchangeable
    templates like "Who This Guide Is For", "Final Checklist", or identical
    section lists copied across articles.

    Output format:
    ---
    lang: {lang}
    title: "Catchy SEO Title about {topic}"
    summary: "Engaging 2-line summary"
    date: "{datetime.now().strftime('%Y-%m-%d')}"
    ---
    (Body content in Markdown)
    """

    try:
        print(f"📡 API 호출 시작: {filename}")
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        content = strip_code_fences(response.text or "")
        ok, errors = validate_generated_markdown(
            content,
            kind="guide",
            lang=lang,
            sibling_exists=filling_sibling,
        )
        if not ok:
            return f"⛔ 품질미달·저장안함: {filename} — {', '.join(errors)}"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"✅ 성공: {filename}"
    except Exception as e:
        return f"❌ 에러: {filename} - {str(e)}"

def run_batch(limit=3):
    missing_tasks = []
    
    # 1. 먼저 생성이 필요한(파일이 없는) 작업 목록을 전부 수집합니다.
    csv_path = _guides_csv_path()
    if not os.path.exists(csv_path):
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_path}")
        return

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            gid = (row.get('id') or '').strip()
            if not gid:
                continue
            dup = duplicate_guide_reason(gid, OUTPUT_DIR)
            if dup:
                print(f"⏭️ 큐에서 제외(중복주제): {gid} — {dup}")
                continue
            for lang in ['en', 'ko']:
                filename = f"{gid}_{lang}.md"
                filepath = os.path.join(OUTPUT_DIR, filename)
                if not os.path.exists(filepath):
                    missing_tasks.append((row, lang))

    # 2. 💡 생성 제한(Limit) 적용
    tasks_to_run = missing_tasks[:limit]

    if not tasks_to_run:
        print("💡 모든 가이드가 이미 생성되어 있습니다. 새로 생성할 항목이 없습니다.")
        _emit_pipeline_result(step="guides", topics=0, generated=0)
        return

    print(f"🚀 총 {len(missing_tasks)}개의 대기 작업 중 상위 {len(tasks_to_run)}개 생성을 시작합니다...")

    workers = max(1, min(limit, 5))
    ok = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(generate_guide, t[0], t[1]) for t in tasks_to_run]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            print(result)
            if result and result.startswith("✅"):
                ok += 1
    topics = len({t[0].get("id") for t in tasks_to_run})
    _emit_pipeline_result(
        step="guides",
        topics=topics,
        generated=ok,
        failed=len(tasks_to_run) - ok,
    )

if __name__ == "__main__":
    env_limit = os.environ.get("GUIDE_LIMIT")
    arg_limit = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        run_limit = int(arg_limit or env_limit or 3)
    except ValueError:
        run_limit = 3
    run_batch(limit=run_limit)
