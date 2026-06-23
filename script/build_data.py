import os
import json
import frontmatter
import markdown
import re
from bs4 import BeautifulSoup
from datetime import datetime
import sys

# ==========================================
# ⚙️ 경로 및 설정
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from seo_priority import CORE_GUIDE_BASES, CORE_ONSEN_IDS, guide_id, prioritize_by_ids
from md_dates import ensure_post_date, save_post

CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')
GUIDE_DIR = os.path.join(CONTENT_DIR, 'guides')
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')

JSON_OUTPUT = os.path.join(STATIC_DIR, 'json', 'onsen_data.json')
SITEMAP_OUTPUT = os.path.join(STATIC_DIR, 'sitemap.xml')
SITEMAP_CORE_OUTPUT = os.path.join(STATIC_DIR, 'sitemap-core.xml')
SITEMAP_LONGTAIL_OUTPUT = os.path.join(STATIC_DIR, 'sitemap-longtail.xml')

BASE_URL = 'https://okonsen.net'
# GCS 이미지 저장소 경로
GCS_IMAGE_BASE = "https://storage.googleapis.com/ok-project-assets/okonsen"


def normalize_markdown_source(raw_text):
    """Normalize malformed markdown before frontmatter parsing."""
    text = raw_text.lstrip('\ufeff')
    text = re.sub(r'^\s*yaml\s*\n(?=---\s*\n)', '', text, count=1, flags=re.IGNORECASE)
    text = re.sub(r'^---\s*\n\{\}\s*\n---\s*\n(?=---\s*\n)', '', text, count=1, flags=re.MULTILINE)
    return text

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
    backfilled = 0
    if not os.path.exists(GUIDE_DIR):
        return guides, backfilled

    for filename in os.listdir(GUIDE_DIR):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(GUIDE_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                post = frontmatter.loads(normalize_markdown_source(f.read()))
            published_date, changed = ensure_post_date(post, filepath)
            if changed:
                save_post(filepath, post)
                backfilled += 1
            guides.append({
                "id": filename.replace('.md', ''),
                "link": f"/guide/{filename.replace('.md', '')}",
                "published": published_date,
            })
        except Exception as e:
            print(f"❌ 가이드 파일 처리 오류 ({filename}): {e}")

    guides.sort(key=lambda x: (x['published'], x['id']), reverse=True)
    return guides, backfilled

def generate_sitemap(onsens, guides, include_static=True):
    """SEO를 위한 사이트맵 XML 생성"""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    last_updated = datetime.now().strftime("%Y-%m-%d")

    if include_static:
        # 메인 페이지
        xml.append('  <url>')
        xml.append(f'    <loc>{BASE_URL}/</loc>')
        xml.append(f'    <lastmod>{last_updated}</lastmod>')
        xml.append('    <priority>1.0</priority>')
        xml.append('  </url>')
        # 허브: 영어 기본 URL + 한국어 변형 (/?lang=en 등은 앱에서 / 로 301)
        static_urls = [
            (f'{BASE_URL}/?lang=ko', '0.9'),
            (f'{BASE_URL}/guides', '0.8'),
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


def split_sitemap_sets(onsens, guides):
    """
    Discovery-only 상태를 줄이기 위해 색인 우선순위용(core)과 후순위(longtail)로 분리.
    - core: GSC 고노출 URL + 최신 URL
    - longtail: 나머지 상세 URL
    """
    priority_guide_ids = [guide_id(base, "en") for base in CORE_GUIDE_BASES] + [
        guide_id(base, "ko") for base in CORE_GUIDE_BASES
    ]
    onsens_ranked = prioritize_by_ids(onsens, CORE_ONSEN_IDS)
    guides_ranked = prioritize_by_ids(guides, priority_guide_ids)

    core_onsens = onsens_ranked[:90]
    longtail_onsens = onsens_ranked[90:]
    core_guides = guides_ranked[:24]
    longtail_guides = guides_ranked[24:]
    return core_onsens, longtail_onsens, core_guides, longtail_guides


def generate_sitemap_index():
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    xml.append('  <sitemap>')
    xml.append(f'    <loc>{BASE_URL}/sitemap-core.xml</loc>')
    xml.append(f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>')
    xml.append('  </sitemap>')
    xml.append('  <sitemap>')
    xml.append(f'    <loc>{BASE_URL}/sitemap-longtail.xml</loc>')
    xml.append(f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>')
    xml.append('  </sitemap>')
    xml.append('</sitemapindex>')
    return '\n'.join(xml)

def main():
    print(f"🔨 데이터 빌드 시작 (최신순 정렬 및 GCS 경로 적용)")
    
    onsens = []
    backfilled = 0
    
    if not os.path.exists(CONTENT_DIR):
        print(f"❌ 컨텐츠 디렉토리를 찾을 수 없습니다: {CONTENT_DIR}")
        return

    # 1. 마크다운 파일 읽기
    for filename in os.listdir(CONTENT_DIR):
        if not filename.endswith('.md'): continue
        
        filepath = os.path.join(CONTENT_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                post = frontmatter.loads(normalize_markdown_source(f.read()))
                
                # 필수 메타데이터 체크
                if post.get('draft') == True: continue
                if not post.get('lat') or not post.get('lng'): continue
                
                published_date, changed = ensure_post_date(post, filepath)
                if changed:
                    save_post(filepath, post)
                    backfilled += 1
                
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
    guides, guide_backfilled = collect_guides()
    backfilled += guide_backfilled
    core_onsens, longtail_onsens, core_guides, longtail_guides = split_sitemap_sets(onsens, guides)
    core_sitemap_content = generate_sitemap(core_onsens, core_guides, include_static=True)
    longtail_sitemap_content = generate_sitemap(longtail_onsens, longtail_guides, include_static=False)
    sitemap_index_content = generate_sitemap_index()

    with open(SITEMAP_CORE_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(core_sitemap_content)
    with open(SITEMAP_LONGTAIL_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(longtail_sitemap_content)
    with open(SITEMAP_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(sitemap_index_content)

    print(f"\n🎉 빌드 완료!")
    if backfilled:
        print(f"   - date 백필: {backfilled}개 MD")
    print(f"   - 처리된 항목: {len(onsens)}개")
    print(f"   - 처리된 가이드: {len(guides)}개")
    print(f"   - 코어 사이트맵: 온천 {len(core_onsens)}개 / 가이드 {len(core_guides)}개")
    print(f"   - 롱테일 사이트맵: 온천 {len(longtail_onsens)}개 / 가이드 {len(longtail_guides)}개")
    print(f"   - 최신 항목: {onsens[0]['title'] if onsens else '없음'} ({onsens[0]['published'] if onsens else '-'})")
    print(f"   - 출력 파일: {JSON_OUTPUT}")

if __name__ == "__main__":
    main()