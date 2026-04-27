import os
import csv
import time
import sys
from datetime import datetime
from google import genai
from dotenv import load_dotenv
import concurrent.futures

# ==========================================
# ⚙️ 설정 (GCS 경로 및 환경 설정)
# ==========================================
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
GCS_IMAGE_BASE = "https://storage.googleapis.com/ok-project-assets/okonsen"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')

TARGET_LANGS = ['en', 'ko']
CATEGORIES = {
    "en": ["Private Bath", "Tattoo OK", "Great View", "Luxury", "Local"],
    "ko": ["가족탕", "타투 허용", "절경", "고급 료칸", "로컬"]
}

def generate_onsen_md(safe_name, name, lat, lng, address, lang, features, agoda_link):
    """Gemini 2.0을 사용한 고퀄리티 컨텐츠 생성 (8000자 지향 및 폰트 크기 최적화)"""
    if not API_KEY: return False
    client = genai.Client(api_key=API_KEY)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    allowed_categories = ", ".join(CATEGORIES.get(lang, CATEGORIES["en"]))
    thumbnail_url = f"{GCS_IMAGE_BASE}/{safe_name}.jpg"

    # 💡 [프롬프트 수정] 제목 태그 제한 및 본문 스타일 지침 추가
    prompt = f"""
    You are an elite travel journalist specializing in Japanese Onsens.
    Write an EXTREMELY comprehensive, deeply detailed guide for '{name}' located at {address}.
    Target Language: {lang}
    Aim for a very long response, around 7,000 to 8,000 characters.

    [Formatting Rules - CRITICAL]
    1. NEVER use the '#' (H1) tag inside the body content.
    2. Use '##' for main sections (History, Baths, etc.).
    3. Use '###' for subsections.
    4. DO NOT wrap an entire paragraph in bold (****). Only bold specific keywords or short phrases.
    5. DO NOT use heading tags for normal sentences.

    Structure:
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
    agoda: "{agoda_link}"
    summary: "3-sentence engaging summary"
    ---
    (Body content in Markdown following the formatting rules above)
    """

    try:
        # 모델명을 최신 버전으로 유지 (gemini-2.0-flash 권장)
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        content = response.text.strip()
        
        # AI가 실수로 넣은 코드 블록 마크업 제거
        content = content.replace("```markdown", "").replace("```", "").strip()

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
    csv_path = os.path.join(SCRIPT_DIR, 'csv', 'onsens.csv')
    if not os.path.exists(csv_path):
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_path}")
        return

    tasks = []
    with open(csv_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if len(tasks) >= limit * 2: break
            name = row.get('Name','').strip()
            if not name: continue
            
            safe_name = name.lower().replace(" ", "_").replace("'", "").replace(",", "")
            
            for lang in TARGET_LANGS:
                filename = f"{safe_name}_{lang}.md"
                if not os.path.exists(os.path.join(CONTENT_DIR, filename)):
                    tasks.append((safe_name, name, row['Lat'], row['Lng'], row['Address'], lang, row['Features'], row['Agoda']))

    if tasks:
        print(f"⚡️ {len(tasks)}개 신규 작업 병렬 실행 시작...")
        # API 할당량에 따라 max_workers 조절 (유료 키의 경우 5~10 적당)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(lambda p: generate_onsen_md(*p), tasks))
    else:
        print("💡 새로 생성할 컨텐츠가 없습니다.")

if __name__ == "__main__":
    # 기본 10개 주제, 인자/환경변수로 오버라이드 가능
    env_limit = os.environ.get("CONTENT_LIMIT")
    arg_limit = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        run_limit = int(arg_limit or env_limit or 10)
    except ValueError:
        run_limit = 10
    process_csv_auto(limit=run_limit)