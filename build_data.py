import os
import json
import frontmatter
import markdown
from bs4 import BeautifulSoup  # HTML 태그 제거용
from datetime import datetime

# 설정
CONTENT_DIR = 'app/content'
JSON_OUTPUT = 'app/static/json/shrines_data.json'
SITEMAP_OUTPUT = 'app/static/sitemap.xml'
BASE_URL = 'https://jinjamap.com'

def strip_markdown(text):
    """
    마크다운 텍스트를 순수 텍스트로 변환하는 함수
    1. 마크다운 -> HTML 변환
    2. HTML -> 텍스트 추출 (태그 제거)
    """
    try:
        # 마크다운을 HTML로 변환
        html = markdown.markdown(text)
        # BeautifulSoup을 이용해 HTML 태그를 모두 제거하고 텍스트만 추출
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()
    except Exception as e:
        print(f"Warning: Text strip failed - {e}")
        return text

def generate_sitemap(shrines):
    """사이트맵 XML 내용을 생성하는 함수"""
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    xml += '  <url>\n'
    xml += f'    <loc>{BASE_URL}/</loc>\n'
    xml += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
    xml += '    <changefreq>daily</changefreq>\n'
    xml += '    <priority>1.0</priority>\n'
    xml += '  </url>\n'

    for shrine in shrines:
        link = shrine['link']
        date_str = shrine['published']
        
        xml += '  <url>\n'
        xml += f'    <loc>{BASE_URL}{link}</loc>\n'
        xml += f'    <lastmod>{date_str}</lastmod>\n'
        xml += '    <changefreq>weekly</changefreq>\n'
        xml += '    <priority>0.8</priority>\n'
        xml += '  </url>\n'
        
    xml += '</urlset>'
    return xml

def main():
    print("🔨 로컬 마크다운 데이터 빌드 시작...")
    
    shrines = []
    
    os.makedirs(os.path.dirname(JSON_OUTPUT), exist_ok=True)
    os.makedirs(os.path.dirname(SITEMAP_OUTPUT), exist_ok=True)

    if not os.path.exists(CONTENT_DIR):
        os.makedirs(CONTENT_DIR)

    for filename in os.listdir(CONTENT_DIR):
        if not filename.endswith('.md'):
            continue
            
        filepath = os.path.join(CONTENT_DIR, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                
                # Draft(초안) 기능 (선택 사항)
                if post.get('draft') == True and not os.environ.get('DEV_MODE'):
                    continue

                if not post.get('lat') or not post.get('lng'):
                    continue

                date_val = post.get('date')
                if date_val:
                    published_date = str(date_val)
                else:
                    published_date = datetime.now().strftime('%Y-%m-%d')

                # [핵심 수정 부분] 요약문 생성 로직 개선
                summary = post.get('summary')
                if not summary:
                    # 마크다운 문법 제거 후 앞부분 120자만 추출
                    clean_text = strip_markdown(post.content)
                    summary = clean_text[:120] + '...'
                
                shrine = {
                    "id": filename.replace('.md', ''),
                    "title": post.get('title', 'No Title'),
                    "lat": post.get('lat'),
                    "lng": post.get('lng'),
                    "categories": post.get('categories', []),
                    "thumbnail": post.get('thumbnail', '/static/images/default.png'),
                    "address": post.get('address', ''),
                    "published": published_date,
                    "summary": summary,  # 정제된 요약문 사용
                    "link": f"/shrine/{filename.replace('.md', '')}" 
                }
                shrines.append(shrine)

        except Exception as e:
            print(f"❌ 에러 발생 ({filename}): {e}")

    shrines.sort(key=lambda x: x['published'], reverse=True)

    final_data = {
        "last_updated": datetime.now().strftime("%Y.%m.%d"),
        "shrines": shrines
    }
    with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    sitemap_content = generate_sitemap(shrines)
    with open(SITEMAP_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(sitemap_content)

    print(f"\n🎉 빌드 완료! 총 {len(shrines)}개")

if __name__ == "__main__":
    main()