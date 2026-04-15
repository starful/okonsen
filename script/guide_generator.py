import os
import csv
import concurrent.futures
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

CSV_PATH = "script/csv/guides.csv" # id, topic_en, topic_ko, keywords
OUTPUT_DIR = "app/content/guides/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_guide(row, lang):
    base_id = row['id']
    topic = row[f'topic_{lang}']
    keywords = row['keywords']
    filename = f"{base_id}_{lang}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(filepath): return f"Skipped: {filename}"

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
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text.strip())
        return f"Success: {filename}"
    except Exception as e:
        return f"Error: {filename} - {str(e)}"

def run_batch():
    tasks = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append((row, 'en'))
            tasks.append((row, 'ko'))

    print(f"🚀 Starting Multi-threaded Generation ({len(tasks)} files)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(generate_guide, t[0], t[1]) for t in tasks]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    run_batch()