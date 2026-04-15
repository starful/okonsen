from flask import Flask, jsonify, render_template, abort, request, redirect
from flask_compress import Compress
import json
import os
import frontmatter
import markdown
import re
import hashlib
import copy

app = Flask(__name__)
Compress(app)

# ==========================================
# 1. 절대 경로 및 데이터 로드
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DATA_FILE = os.path.join(STATIC_DIR, 'json', 'onsen_data.json')
CONTENT_DIR = os.path.join(BASE_DIR, 'content')
GUIDE_DIR = os.path.join(CONTENT_DIR, 'guides')

# 서버 시작 시 JSON 데이터 로드
CACHED_DATA = {"onsens": [], "last_updated": "2026.03.19"}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            CACHED_DATA = json.load(f)
            print(f"✅ 온천 데이터 로드 완료: {len(CACHED_DATA.get('onsens', []))}개")
    except Exception as e:
        print(f"❌ 데이터 로드 오류: {e}")

# ==========================================
# 2. 이미지 매핑 및 파싱 로직
# ==========================================
GUIDE_IMAGES = [
    "https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=1000",
    "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?q=80&w=1000",
    "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?q=80&w=1000",
    "https://images.unsplash.com/photo-1526481280693-3bfa7568e0f3?q=80&w=1000"
    # 1. 온천/물 안개 (전형적인 온천 느낌)
    "https://images.unsplash.com/photo-1545569341-9eb8b30979d9?q=80&w=1000",
    # 3. 후지산과 충령탑 (일본의 상징)
    "https://images.unsplash.com/photo-1528360983277-13d401cdc186?q=80&w=1000",
    # 4. 정갈한 가이세키/일식 요리
    "https://images.unsplash.com/photo-1580822184713-fc5400e7fe10?q=80&w=1000",
    # 5. 교토의 밤거리 (다이쇼 로망 느낌)
    "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?q=80&w=1000",
    # 7. 료칸 내부 다다미 방 (고급스러운 휴식)
    "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?q=80&w=1000",
    # 8. 대나무 숲 (치유/힐링 테마)
    "https://images.unsplash.com/photo-1518709766631-a6a7f45921c3?q=80&w=1000",
    # 9. 일본식 정원 (젠 스타일)
    "https://images.unsplash.com/photo-1596395819057-e37f55a8516b?q=80&w=1000",
    # 10. 따뜻한 라멘/길거리 음식
    "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?q=80&w=1000",
    # 11. 교토의 붉은 신사 (전통 문화)
    "https://images.unsplash.com/photo-1478436127897-769e1b3f0f36?q=80&w=1000",
    # 13. 산속의 고즈넉한 풍경
    "https://images.unsplash.com/photo-1526481280693-3bfa7568e0f3?q=80&w=1000",
    # 14. 벚꽃과 어우러진 성 (봄 테마)
    "https://images.unsplash.com/photo-1524230572899-a752b3835840?q=80&w=1000",
    # 15. 일본 전통 차/다도 (오모테나시)
    "https://images.unsplash.com/photo-1576092768241-dec231879fc3?q=80&w=1000"
]


def get_mapped_image(base_id):
    idx = int(hashlib.md5(base_id.encode()).hexdigest(), 16) % len(GUIDE_IMAGES)
    return GUIDE_IMAGES[idx]

def get_footer_stats(lang):
    """모든 페이지에서 풋터 수치가 0이 되지 않도록 실시간 계산"""
    data_list = CACHED_DATA.get('onsens', [])
    filtered_count = len([o for o in data_list if o.get('lang') == lang])
    return {
        "total_onsens": filtered_count if filtered_count > 0 else len(data_list) // 2,
        "last_updated": CACHED_DATA.get('last_updated', '2026.03.19')
    }

def get_all_guides(lang):
    guides = []
    if not os.path.exists(GUIDE_DIR): return guides
    
    # 1. 먼저 모든 가이드 파일을 읽어 리스트에 담습니다.
    raw_guides = []
    for f in os.listdir(GUIDE_DIR):
        if f.endswith(f"_{lang}.md"):
            path = os.path.join(GUIDE_DIR, f)
            base_id = f.replace(f"_{lang}.md", "")
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    raw_text = file.read()
                    post = frontmatter.loads(raw_text)
                    title = post.get('title')
                    summary = post.get('summary')
                    
                    if not title or title == "None":
                        title_match = re.search(r'title:\s*"(.*?)"', raw_text)
                        title = title_match.group(1) if title_match else "Travel Guide"
                    if not summary or summary == "None":
                        summary_match = re.search(r'summary:\s*"(.*?)"', raw_text)
                        summary = summary_match.group(1) if summary_match else post.content[:150].replace('\n', ' ')
                    
                    raw_guides.append({
                        "id": f.replace('.md', ''),
                        "base_id": base_id,
                        "title": title,
                        "summary": summary,
                        "date": str(post.get('date', '2024-01-01'))
                    })
            except: continue

    # 2. 날짜 역순(최신순)으로 정렬합니다.
    sorted_guides = sorted(raw_guides, key=lambda x: x['date'], reverse=True)

    # 3. 정렬된 리스트를 돌면서 이미지를 할당하되, 이전 이미지와 겹치면 인덱스를 조정합니다.
    last_img_idx = -1
    for item in sorted_guides:
        # 기본 해시 기반 인덱스 계산
        img_idx = int(hashlib.md5(item['base_id'].encode()).hexdigest(), 16) % len(GUIDE_IMAGES)
        
        # 💡 중복 방지 핵심 로직: 이전 가이드와 이미지가 같다면 다음 이미지 선택
        if img_idx == last_img_idx:
            img_idx = (img_idx + 1) % len(GUIDE_IMAGES)
        
        item['image'] = GUIDE_IMAGES[img_idx]
        last_img_idx = img_idx
        guides.append(item)

    return guides

# ==========================================
# 3. API Spoofing (카테고리 매핑 포함)
# ==========================================
CATEGORY_MAPPING = {
    "가족탕": "Private Bath", "타투 허용": "Tattoo OK", "절경": "Great View",
    "고급 료칸": "Luxury", "고급": "Luxury", "로컬": "Local"
}

@app.route('/api/onsens')
def api_onsens():
    requested_lang = request.args.get('lang', 'en')
    data_list = CACHED_DATA.get('onsens', [])
    filtered = [o for o in data_list if o.get('lang') == requested_lang]
    if not filtered: filtered = [o for o in data_list if o.get('lang') == 'en']

    spoofed_list = []
    for onsen in filtered:
        spoofed = copy.deepcopy(onsen)
        spoofed['lang'] = 'en' # JS Spoofing
        new_cats = [CATEGORY_MAPPING.get(c.strip(), c.strip()) for c in spoofed.get('categories', [])]
        spoofed['categories'] = list(set(new_cats))
        spoofed_list.append(spoofed)
    return jsonify({"onsens": spoofed_list, "last_updated": CACHED_DATA.get('last_updated')})

# ==========================================
# 4. 라우팅 (모든 페이지에 Footer 데이터 주입)
# ==========================================
@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    top_guides = get_all_guides(lang)[:3]
    stats = get_footer_stats(lang)
    return render_template('index.html', lang=lang, guides=top_guides, **stats)

@app.route('/guides')
def guide_list():
    lang = request.args.get('lang', 'en')
    all_guides = get_all_guides(lang)
    stats = get_footer_stats(lang)
    return render_template('guide_list.html', guides=all_guides, lang=lang, **stats)

@app.route('/guide/<guide_id>')
def guide_detail(guide_id):
    lang = request.args.get('lang', 'en')
    path = os.path.join(GUIDE_DIR, f"{guide_id}.md")
    if not os.path.exists(path): abort(404)
    
    with open(path, 'r', encoding='utf-8') as f:
        raw_content = f.read()
        post = frontmatter.loads(raw_content)
        title = post.get('title')
        body = post.content
        if not title or title == "None":
            title_match = re.search(r'title:\s*"(.*?)"', raw_content)
            title = title_match.group(1) if title_match else "Travel Guide"

        # 본문 설정값/코드블록 제거
        body = re.sub(r'---.*?---', '', body, flags=re.DOTALL)
        body = body.replace('```markdown', '').replace('```', '').strip()

    content_html = markdown.markdown(body, extensions=['tables', 'toc', 'fenced_code'])
    base_id = guide_id.rsplit('_', 1)[0]
    image_url = get_mapped_image(base_id)
    stats = get_footer_stats(lang)

    return render_template('guide_detail.html', 
                           title=title, content=content_html, lang=lang, 
                           image_url=image_url, base_id=base_id, **stats)

@app.route('/onsen/<onsen_id>')
def onsen_detail(onsen_id):
    md_path = os.path.join(CONTENT_DIR, f"{onsen_id}.md")
    if not os.path.exists(md_path): abort(404)
    with open(md_path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    if isinstance(post.get('categories'), str):
        post['categories'] = [c.strip() for c in post['categories'].split(',')]

    content_html = markdown.markdown(post.content, extensions=['tables'])
    stats = get_footer_stats(post.get('lang', 'en'))
    return render_template('detail.html', post=post, content=content_html, **stats)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)