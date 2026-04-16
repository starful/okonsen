import os
import csv
import time
from datetime import datetime
from google import genai
from dotenv import load_dotenv
import concurrent.futures

# ==========================================
# ⚙️ 설정 (GCS 경로 추가)
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
    """Gemini 2.0을 사용한 고퀄리티 컨텐츠 생성 (8000자 지향)"""
    if not API_KEY: return False
    client = genai.Client(api_key=API_KEY)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    allowed_categories = ", ".join(CATEGORIES.get(lang, CATEGORIES["en"]))
    thumbnail_url = f"{GCS_IMAGE_BASE}/{safe_name}.jpg" # GCS 경로 사용

    prompt = f"""
    You are an elite travel journalist specializing in Japanese Onsens.
    Write an EXTREMELY comprehensive, deeply detailed guide for '{name}'.
    Target Language: {lang}
    Aim for 7,000 to 8,000 characters.

    Structure:
    - Introduction (vibe and first impression)
    - History & Tradition of the area/ryokan
    - Deep Dive into the Baths (Rotemburo, minerals, views)
    - Rooms & Architecture (Wabi-sabi aesthetics)
    - Gastronomy (Kaiseki dinner details)
    - Local Attractions around {address}
    - Practical Tips (Tattoo policy, best season)
    - Access Guide

    Output MUST be in this YAML format:
    ---
    lang: {lang}
    title: "Catchy SEO Title"
    lat: {lat}
    lng: {lng}
    categories: ["Category 1", "Category 2"]
    thumbnail: "{thumbnail_url}"
    address: "{address}"
    date: "{current_date}"
    agoda: "{agoda_link}"
    summary: "3-sentence engaging summary"
    ---
    (Body content in Markdown)
    """

    try:
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        content = response.text.strip()
        # 코드블록 마크업 제거
        content = content.replace("```markdown", "").replace("```", "").strip()

        filepath = os.path.join(CONTENT_DIR, f"{safe_name}_{lang}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ [완료] {safe_name}_{lang}.md ({len(content)}자)")
        return True
    except Exception as e:
        print(f"❌ [에러] {name}: {e}")
        return False

def process_csv_auto(limit=10):
    csv_path = os.path.join(SCRIPT_DIR, 'csv', 'onsens.csv')
    if not os.path.exists(csv_path): return

    tasks = []
    with open(csv_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if len(tasks) >= limit * 2: break
            name = row.get('Name','').strip()
            safe_name = name.lower().replace(" ", "_").replace("'", "").replace(",", "")
            
            for lang in TARGET_LANGS:
                if not os.path.exists(os.path.join(CONTENT_DIR, f"{safe_name}_{lang}.md")):
                    tasks.append((safe_name, name, row['Lat'], row['Lng'], row['Address'], lang, row['Features'], row['Agoda']))

    if tasks:
        print(f"⚡️ {len(tasks)}개 작업 병렬 실행 시작...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(lambda p: generate_onsen_md(*p), tasks))

if __name__ == "__main__":
    process_csv_auto(limit=5)