import os
import json
import frontmatter
import markdown
from bs4 import BeautifulSoup
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')

JSON_OUTPUT = os.path.join(STATIC_DIR, 'json', 'onsen_data.json')
SITEMAP_OUTPUT = os.path.join(STATIC_DIR, 'sitemap.xml')

BASE_URL = 'https://okonsen.net'
GCS_IMAGE_BASE = "https://storage.googleapis.com/ok-project-assets/okonsen"

def strip_markdown(text):
    try:
        html = markdown.markdown(text)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()
    except: return text

def generate_sitemap(onsens):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    last_updated = datetime.now().strftime("%Y-%m-%d")
    xml.append(f'  <url><loc>{BASE_URL}/</loc><lastmod>{last_updated}</lastmod><priority>1.0</priority></url>')

    for onsen in onsens:
        link = onsen['link']
        date_str = onsen.get('published', last_updated)
        xml.append(f'  <url><loc>{BASE_URL}{link}</loc><lastmod>{date_str}</lastmod><priority>0.8</priority></url>')
    xml.append('</urlset>')
    return '\n'.join(xml)

def main():
    print(f"🔨 데이터 빌드 시작 (GCS 경로 및 사이트맵 생성)")
    onsens = []
    if not os.path.exists(CONTENT_DIR): return

    for filename in os.listdir(CONTENT_DIR):
        if not filename.endswith('.md'): continue
        filepath = os.path.join(CONTENT_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                if post.get('draft') == True or not post.get('lat'): continue
                
                # 썸네일 경로를 GCS로 강제 전환
                raw_thumb = post.get('thumbnail', 'default.png')
                img_name = os.path.basename(raw_thumb)
                gcs_thumb_url = f"{GCS_IMAGE_BASE}/{img_name}"

                # 카테고리 리스트화
                raw_cats = post.get('categories', [])
                categories = [c.strip() for c in raw_cats.split(',')] if isinstance(raw_cats, str) else raw_cats

                onsens.append({
                    "id": filename.replace('.md', ''),
                    "lang": post.get('lang', 'en'),
                    "title": post.get('title', 'No Title'),
                    "lat": post.get('lat'),
                    "lng": post.get('lng'),
                    "categories": categories,
                    "thumbnail": gcs_thumb_url,
                    "address": post.get('address', ''),
                    "published": str(post.get('date', datetime.now().strftime('%Y-%m-%d'))),
                    "summary": post.get('summary', strip_markdown(post.content)[:120] + '...'),
                    "link": f"/onsen/{filename.replace('.md', '')}"
                })
        except Exception as e: print(f"❌ Error {filename}: {e}")

    onsens.sort(key=lambda x: x['published'], reverse=True)
    
    # JSON 저장
    final_data = {"last_updated": datetime.now().strftime("%Y.%m.%d"), "onsens": onsens}
    with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    # 사이트맵 저장
    sitemap_content = generate_sitemap(onsens)
    with open(SITEMAP_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(sitemap_content)

    print(f"✅ 빌드 완료: {len(onsens)}개 온천 데이터 및 사이트맵 생성됨.")

if __name__ == "__main__":
    main()