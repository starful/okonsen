import os
import json
import frontmatter
import markdown
from bs4 import BeautifulSoup
from datetime import datetime

# ==========================================
# ⚙️ 경로 및 설정
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')
GUIDE_DIR = os.path.join(CONTENT_DIR, 'guides')
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')

JSON_OUTPUT = os.path.join(STATIC_DIR, 'json', 'onsen_data.json')
SITEMAP_OUTPUT = os.path.join(STATIC_DIR, 'sitemap.xml')

BASE_URL = 'https://okonsen.net'
# GCS 이미지 저장소 경로
GCS_IMAGE_BASE = "https://storage.googleapis.com/ok-project-assets/okonsen"

def strip_markdown(text):
    """마크다운을 일반 텍스트로 변환하여 요약문 생성"""
    try:
        html = markdown.markdown(text)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text().strip()
    except:
        return text

def collect_guides():
    guides = []
    if not os.path.exists(GUIDE_DIR):
        return guides

    for filename in os.listdir(GUIDE_DIR):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(GUIDE_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                date_val = post.get('date')
                published_date = str(date_val) if date_val else datetime.now().strftime('%Y-%m-%d')
                guides.append({
                    "id": filename.replace('.md', ''),
                    "link": f"/guide/{filename.replace('.md', '')}",
                    "published": published_date,
                })
        except Exception as e:
            print(f"❌ 가이드 파일 처리 오류 ({filename}): {e}")

    guides.sort(key=lambda x: (x['published'], x['id']), reverse=True)
    return guides

def generate_sitemap(onsens, guides):
    """SEO를 위한 사이트맵 XML 생성"""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    last_updated = datetime.now().strftime("%Y-%m-%d")

    # 메인 페이지
    xml.append('  <url>')
    xml.append(f'    <loc>{BASE_URL}/</loc>')
    xml.append(f'    <lastmod>{last_updated}</lastmod>')
    xml.append('    <priority>1.0</priority>')
    xml.append('  </url>')

    # 언어별 메인/가이드 목록 페이지
    static_urls = [
        (f'{BASE_URL}/?lang=en', '0.9'),
        (f'{BASE_URL}/?lang=ko', '0.9'),
        (f'{BASE_URL}/guides?lang=en', '0.8'),
        (f'{BASE_URL}/guides?lang=ko', '0.8'),
    ]
    for loc, priority in static_urls:
        xml.append('  <url>')
        xml.append(f'    <loc>{loc}</loc>')
        xml.append(f'    <lastmod>{last_updated}</lastmod>')
        xml.append(f'    <priority>{priority}</priority>')
        xml.append('  </url>')

    # 각 온천 상세 페이지
    seen_onsen_links = set()
    for onsen in onsens:
        link = onsen['link']
        if link in seen_onsen_links:
            continue
        seen_onsen_links.add(link)
        date_str = onsen.get('published', last_updated)
        xml.append('  <url>')
        xml.append(f'    <loc>{BASE_URL}{link}</loc>')
        xml.append(f'    <lastmod>{date_str}</lastmod>')
        xml.append('    <priority>0.8</priority>')
        xml.append('  </url>')

    # 가이드 상세 페이지
    for guide in guides:
        xml.append('  <url>')
        xml.append(f'    <loc>{BASE_URL}{guide["link"]}</loc>')
        xml.append(f'    <lastmod>{guide.get("published", last_updated)}</lastmod>')
        xml.append('    <priority>0.7</priority>')
        xml.append('  </url>')

    xml.append('</urlset>')
    return '\n'.join(xml)

def main():
    print(f"🔨 데이터 빌드 시작 (최신순 정렬 및 GCS 경로 적용)")
    
    onsens = []
    
    if not os.path.exists(CONTENT_DIR):
        print(f"❌ 컨텐츠 디렉토리를 찾을 수 없습니다: {CONTENT_DIR}")
        return

    # 1. 마크다운 파일 읽기
    for filename in os.listdir(CONTENT_DIR):
        if not filename.endswith('.md'): continue
        
        filepath = os.path.join(CONTENT_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                
                # 필수 메타데이터 체크
                if post.get('draft') == True: continue
                if not post.get('lat') or not post.get('lng'): continue
                
                # 날짜 처리 (정렬의 핵심)
                date_val = post.get('date')
                # YYYY-MM-DD 형식이 아니거나 없는 경우 오늘 날짜로 대체
                published_date = str(date_val) if date_val else datetime.now().strftime('%Y-%m-%d')
                
                # 요약문 처리
                summary = post.get('summary')
                if not summary or summary == "None":
                    summary = strip_markdown(post.content)[:120] + '...'

                # 카테고리 처리 (문자열인 경우 리스트로 변환)
                raw_categories = post.get('categories', [])
                if isinstance(raw_categories, str):
                    categories = [c.strip() for c in raw_categories.split(',')]
                else:
                    categories = raw_categories

                # 썸네일 경로를 GCS 주소로 강제 변환
                raw_thumb = post.get('thumbnail', 'default.png')
                img_name = os.path.basename(raw_thumb)
                gcs_thumbnail_url = f"{GCS_IMAGE_BASE}/{img_name}"

                onsen = {
                    "id": filename.replace('.md', ''),
                    "lang": post.get('lang', 'en'),
                    "title": post.get('title', 'No Title'),
                    "lat": post.get('lat'),
                    "lng": post.get('lng'),
                    "categories": categories,
                    "thumbnail": gcs_thumbnail_url,
                    "address": post.get('address', ''),
                    "published": published_date,
                    "summary": summary,
                    "link": f"/onsen/{filename.replace('.md', '')}"
                }
                onsens.append(onsen)
        except Exception as e:
            print(f"❌ 파일 처리 오류 ({filename}): {e}")

    # 2. 💡 최신순 정렬 (날짜 기준 내림차순, 날짜 같으면 ID 역순)
    onsens.sort(key=lambda x: (x['published'], x['id']), reverse=True)

    # 3. JSON 데이터 생성
    final_data = {
        "last_updated": datetime.now().strftime("%Y.%m.%d %H:%M"),
        "onsens": onsens
    }
    
    os.makedirs(os.path.dirname(JSON_OUTPUT), exist_ok=True)
    with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    # 4. 사이트맵 생성
    guides = collect_guides()
    sitemap_content = generate_sitemap(onsens, guides)
    with open(SITEMAP_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(sitemap_content)

    print(f"\n🎉 빌드 완료!")
    print(f"   - 처리된 항목: {len(onsens)}개")
    print(f"   - 처리된 가이드: {len(guides)}개")
    print(f"   - 최신 항목: {onsens[0]['title'] if onsens else '없음'} ({onsens[0]['published'] if onsens else '-'})")
    print(f"   - 출력 파일: {JSON_OUTPUT}")

if __name__ == "__main__":
    main()