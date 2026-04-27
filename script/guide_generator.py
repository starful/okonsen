import os
import csv
import sys
import concurrent.futures
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

CSV_PATH = "script/csv/guides.csv"
OUTPUT_DIR = "app/content/guides/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_guide(row, lang):
    base_id = row['id']
    topic = row[f'topic_{lang}']
    keywords = row['keywords']
    filename = f"{base_id}_{lang}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # 본문 생성 프롬프트
    prompt = f"""
    Write an exhaustive, professional SEO travel guide about '{topic}' in Japan.
    Target Language: {lang}
    Keywords to include: {keywords}
    Length: At least 4,000 characters.

    Structure:
    1. Deep introduction.
    2. Historical context or cultural significance.
    3. Practical 'How-to' or 'Where-to' tips.
    4. Expert recommendations.
    5. Conclusion.

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
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text.strip())
        return f"✅ 성공: {filename}"
    except Exception as e:
        return f"❌ 에러: {filename} - {str(e)}"

def run_batch(limit=3):
    missing_tasks = []
    
    # 1. 먼저 생성이 필요한(파일이 없는) 작업 목록을 전부 수집합니다.
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV 파일을 찾을 수 없습니다: {CSV_PATH}")
        return

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for lang in ['en', 'ko']:
                filename = f"{row['id']}_{lang}.md"
                filepath = os.path.join(OUTPUT_DIR, filename)
                if not os.path.exists(filepath):
                    missing_tasks.append((row, lang))

    # 2. 💡 생성 제한(Limit) 적용
    tasks_to_run = missing_tasks[:limit]

    if not tasks_to_run:
        print("💡 모든 가이드가 이미 생성되어 있습니다. 새로 생성할 항목이 없습니다.")
        return

    print(f"🚀 총 {len(missing_tasks)}개의 대기 작업 중 상위 {len(tasks_to_run)}개 생성을 시작합니다...")

    # 3. 멀티스레딩 실행
    workers = max(1, min(limit, 5))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(generate_guide, t[0], t[1]) for t in tasks_to_run]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    env_limit = os.environ.get("GUIDE_LIMIT")
    arg_limit = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        run_limit = int(arg_limit or env_limit or 3)
    except ValueError:
        run_limit = 3
    run_batch(limit=run_limit)