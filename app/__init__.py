from flask import Flask, jsonify, render_template, abort, request, redirect, send_from_directory, Response
from flask_compress import Compress
import json
import os
import frontmatter
import markdown
import re
import hashlib
import copy
import io
import urllib.request
from typing import List, Dict
from dotenv import load_dotenv

CORE_GUIDE_BASES = [
    "tattoo_friendly_onsen_list",
    "kurokawa_hidden_gems",
    "tattoo_friendly_master_list",
    "onsen_etiquette_basics",
    "onsen_etiquette_guide",
    "hakone_area_deep_dive",
    "private_bath_kashikiri",
    "beppu_hell_tour_guide",
]
CORE_ONSEN_IDS = [
    "kusatsu_onsen_ryokan_yoshinoya_en",
    "kusatsu_onsen_ryokan_yoshinoya_ko",
    "kurokawa_onsen_hozantei_en",
    "the_prince_hakone_lake_ashinoko_en",
    "the_prince_hakone_lake_ashinoko_ko",
    "yufuin_onsen_yufuin-so_en",
    "yufuin_onsen_yufuin-so_ko",
]

app = Flask(__name__)
Compress(app)

try:
    from .reactions import reactions_bp
except ImportError:
    from reactions import reactions_bp

app.register_blueprint(reactions_bp)

SITE_URL = os.environ.get("SITE_URL", "https://okonsen.net").rstrip("/")
GCS_ASSET_PREFIX = "okonsen"


def _gcs_image_url(filename: str) -> str:
    return f"https://storage.googleapis.com/ok-project-assets/{GCS_ASSET_PREFIX}/{filename}"


def _social_image_url(base_id: str) -> str:
    safe = re.sub(r"[^a-z0-9_-]", "", base_id.lower())
    return f"{SITE_URL}/social/{safe}.jpg"


def _og_image_context(base_id: str) -> dict:
    og_image_abs = _social_image_url(base_id)
    return {
        "og_image_abs": og_image_abs,
        "og_image_width": 1200,
        "og_image_height": 630,
    }


def _card_path(onsen_id: str) -> str:
    return f"/card/{onsen_id}"


def _jpeg_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=78, optimize=True, progressive=True)
    return buf.getvalue()


def _linkedin_inspector_url(page_url: str) -> str:
    from urllib.parse import quote
    return f"https://www.linkedin.com/post-inspector/inspect/{quote(page_url, safe='')}"


def _share_context(slug: str, title: str, lang: str, page_path: str, base_id: str = "") -> dict:
    share_url = f"{SITE_URL}{page_path}"
    share_url_x = f"{SITE_URL}{_card_path(slug)}"
    if lang == "ko":
        share_tweet = f"{title} — OKOnsen"
    else:
        share_tweet = f"{title} — Japan onsen guide on OKOnsen"
    return {
        "share_id": slug,
        "share_url": share_url,
        "share_url_x": share_url_x,
        "share_tweet": share_tweet,
        "share_lang": lang if lang in ("en", "ko") else "en",
        "og_page_url": share_url,
        "linkedin_inspector_url": _linkedin_inspector_url(share_url),
    }

# Load .env from project root for local development.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Backward compatibility:
# - GOOGLE_MAPS_API_KEY: recommended variable name for browser maps key
# - GOOGLE_PLACES_API_KEY: legacy variable name used in this project
GOOGLE_MAPS_API_KEY = (
    os.environ.get('GOOGLE_MAPS_API_KEY')
    or os.environ.get('GOOGLE_PLACES_API_KEY')
    or ''
).strip()

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

def prioritize_by_ids(items, priority_ids, id_key="id"):
    priority_set = set(priority_ids)
    priority_map = {pid: idx for idx, pid in enumerate(priority_ids)}
    prioritized = [x for x in items if x.get(id_key) in priority_set]
    remaining = [x for x in items if x.get(id_key) not in priority_set]
    prioritized.sort(key=lambda x: priority_map.get(x.get(id_key), 999))
    return prioritized + remaining


def get_featured_onsens(lang, limit=12):
    """서버사이드 내부 링크용 온천 목록(크롤러가 바로 따라갈 수 있는 링크)"""
    data_list = CACHED_DATA.get('onsens', [])
    filtered = [o for o in data_list if o.get('lang') == lang]
    if not filtered:
        filtered = [o for o in data_list if o.get('lang') == 'en']
    lang_ids = [oid for oid in CORE_ONSEN_IDS if oid.endswith(f"_{lang}")]
    ranked = prioritize_by_ids(filtered, lang_ids)
    return ranked[:limit]


def _resolve_lang_slug_redirect(prefix: str, slug: str, content_dir: str):
    """Redirect /guide/base or /onsen/base to the canonical *_en/*_ko URL."""
    if not slug or slug.endswith("_en") or slug.endswith("_ko"):
        return None
    en_path = os.path.join(content_dir, f"{slug}_en.md")
    ko_path = os.path.join(content_dir, f"{slug}_ko.md")
    if os.path.exists(en_path):
        return redirect(f"{prefix}/{slug}_en", code=301)
    if os.path.exists(ko_path):
        return redirect(f"{prefix}/{slug}_ko", code=301)
    return None


def get_priority_guides(lang, limit=8):
    """GSC 고노출 가이드를 홈/허브에서 우선 노출."""
    guides = get_all_guides(lang)
    ordered = []
    for base in CORE_GUIDE_BASES:
        target_id = f"{base}_{lang}"
        for g in guides:
            if g.get("id") == target_id:
                ordered.append(g)
                break
    return ordered[:limit]


def normalize_markdown_source(raw_text: str) -> str:
    """Normalize malformed markdown sources before frontmatter parsing."""
    text = raw_text.lstrip('\ufeff')
    # Some generated files start with a stray "yaml" line before frontmatter.
    text = re.sub(r'^\s*yaml\s*\n(?=---\s*\n)', '', text, count=1, flags=re.IGNORECASE)
    # Remove empty frontmatter stub if followed by real frontmatter.
    text = re.sub(r'^---\s*\n\{\}\s*\n---\s*\n(?=---\s*\n)', '', text, count=1, flags=re.MULTILINE)
    return text


def extract_faq_items(body: str, limit: int = 6) -> List[Dict[str, str]]:
    """Extract Q/A pairs from markdown body for FAQPage schema."""
    pattern = re.compile(
        r'\*\*Q\d*[:：]\s*(.*?)\*\*\s*\nA[:：]\s*(.*?)(?=\n\s*\*\*Q\d*[:：]|\Z)',
        re.DOTALL
    )
    faqs = []
    for q, a in pattern.findall(body):
        q_clean = re.sub(r'\s+', ' ', q).strip()
        a_clean = re.sub(r'\s+', ' ', a).strip()
        if q_clean and a_clean:
            faqs.append({"question": q_clean, "answer": a_clean})
        if len(faqs) >= limit:
            break
    return faqs

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
                    raw_text = normalize_markdown_source(file.read())
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
    sorted_guides = sorted(raw_guides, key=lambda x: (x['date'], x['id']), reverse=True)

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


@app.before_request
def seo_url_normalization():
    if request.method not in ("GET", "HEAD"):
        return None
    p = request.path
    if p.startswith("/static/") or p.startswith("/api/"):
        return None
    if p in ("/sitemap.xml", "/sitemap-core.xml", "/sitemap-longtail.xml", "/robots.txt"):
        return None
    if request.headers.get("X-Forwarded-Proto", "").lower() == "http":
        return redirect(request.url.replace("http://", "https://", 1), code=301)
    args = request.args
    keys = set(args.keys())
    if p == "/" and keys == {"lang"} and args.get("lang") == "en":
        return redirect("/", code=301)
    if p == "/guides" and keys == {"lang"} and args.get("lang") == "en":
        return redirect("/guides", code=301)
    if p in ("/about.html", "/privacy.html"):
        return redirect(p.replace(".html", ""), code=301)

    if p.startswith("/guide/") and len(p) > len("/guide/"):
        slug = p.rsplit("/", 1)[-1]
        # /guide/<base> -> /guide/<base>_en|_ko
        target = _resolve_lang_slug_redirect("/guide", slug, GUIDE_DIR)
        if target:
            return target
        # /guide/<id>?lang=xx -> strip query (language is already in path)
        if keys == {"lang"}:
            return redirect(p, code=301)
    if p.startswith("/onsen/") and len(p) > len("/onsen/"):
        slug = p.rsplit("/", 1)[-1]
        target = _resolve_lang_slug_redirect("/onsen", slug, CONTENT_DIR)
        if target:
            return target
        if keys == {"lang"}:
            return redirect(p, code=301)
    return None


try:
    from .family_sites import cross_links_for, inject_family_context
except ImportError:
    from family_sites import cross_links_for, inject_family_context

FAMILY_SITE_ID = "okonsen"


@app.context_processor
def inject_family_sites():
    lang = request.args.get("lang", "en") if request else "en"
    return inject_family_context(FAMILY_SITE_ID, lang)


@app.route('/sitemap.xml')
def sitemap_xml():
    """Search Console / crawlers expect https://okonsen.net/sitemap.xml (see robots.txt)."""
    return send_from_directory(STATIC_DIR, 'sitemap.xml', mimetype='application/xml')


@app.route('/sitemap-core.xml')
def sitemap_core_xml():
    return send_from_directory(STATIC_DIR, 'sitemap-core.xml', mimetype='application/xml')


@app.route('/sitemap-longtail.xml')
def sitemap_longtail_xml():
    return send_from_directory(STATIC_DIR, 'sitemap-longtail.xml', mimetype='application/xml')


@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(STATIC_DIR, 'robots.txt', mimetype='text/plain')


@app.route('/favicon.ico')
def favicon_ico():
    return redirect('/static/images/favicons.ico', code=301)


@app.route('/static/images/<path:filename>')
def serve_images(filename):
    """이미지는 GCS가 기준 — okadmin 업로드 즉시 반영."""
    images_root = os.path.join(STATIC_DIR, 'images')
    if any(x in filename for x in ['favicon', 'apple-touch']):
        local_path = os.path.join(images_root, filename)
        if os.path.isfile(local_path):
            return send_from_directory(images_root, filename)
    url = f"https://storage.googleapis.com/ok-project-assets/okonsen/{filename}"
    if request.query_string:
        url = f"{url}?{request.query_string.decode()}"
    return redirect(url, code=302)


@app.route('/social/<slug>.jpg')
def social_image(slug):
    """Serve onsen thumbnail on-site for OG/Twitter (1200×630 JPEG, no redirect)."""
    safe = re.sub(r"[^a-z0-9_-]", "", slug.lower())
    if not safe:
        abort(404)
    gcs_url = _gcs_image_url(f"{safe}.jpg")
    try:
        with urllib.request.urlopen(gcs_url, timeout=15) as resp:
            raw = resp.read()
            if not raw:
                abort(404)
    except Exception:
        abort(404)

    try:
        from PIL import Image, ImageOps

        img = Image.open(io.BytesIO(raw)).convert("RGB")
        data = _jpeg_bytes(ImageOps.fit(img, (1200, 630), Image.Resampling.LANCZOS))
    except Exception:
        data = raw

    return Response(
        data,
        mimetype="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.route('/about')
@app.route('/about.html')
def about_page():
    return render_template('about.html')


@app.route('/privacy')
@app.route('/privacy.html')
def privacy_page():
    return render_template('privacy.html')


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
    priority_guides = get_priority_guides(lang, limit=3)
    top_guides = priority_guides if priority_guides else get_all_guides(lang)[:3]
    boost_guides = get_priority_guides(lang, limit=8)
    featured_onsens = get_featured_onsens(lang)
    stats = get_footer_stats(lang)
    return render_template(
        'index.html',
        lang=lang,
        guides=top_guides,
        boost_guides=boost_guides,
        featured_onsens=featured_onsens,
        google_maps_api_key=GOOGLE_MAPS_API_KEY,
        **stats
    )

@app.route('/guides')
def guide_list():
    lang = request.args.get('lang', 'en')
    all_guides = get_all_guides(lang)
    boost_guides = get_priority_guides(lang, limit=8)
    stats = get_footer_stats(lang)
    return render_template('guide_list.html', guides=all_guides, boost_guides=boost_guides, lang=lang, **stats)

@app.route('/guide/<guide_id>')
def guide_detail(guide_id):
    inferred_lang = "ko" if guide_id.endswith("_ko") else "en"
    lang = request.args.get("lang", inferred_lang)
    if lang not in ("en", "ko"):
        lang = inferred_lang
    path = os.path.join(GUIDE_DIR, f"{guide_id}.md")
    if not os.path.exists(path): abort(404)
    
    with open(path, 'r', encoding='utf-8') as f:
        raw_content = normalize_markdown_source(f.read())
        post = frontmatter.loads(raw_content)
        title = post.get('title')
        summary = post.get('summary')
        body = post.content
        if not title or title == "None":
            title_match = re.search(r'title:\s*"(.*?)"', raw_content)
            title = title_match.group(1) if title_match else "Travel Guide"
        if not summary or summary == "None":
            summary = post.content[:160].replace('\n', ' ').strip()

        # 본문 설정값/코드블록 제거
        body = re.sub(r'---.*?---', '', body, flags=re.DOTALL)
        body = body.replace('```markdown', '').replace('```', '').strip()
        body = re.sub(r'\(Agoda 링크는 .*?예정입니다\.\)', '', body, flags=re.IGNORECASE)

    content_html = markdown.markdown(body, extensions=['tables', 'toc', 'fenced_code'])
    base_id = guide_id.rsplit('_', 1)[0]
    image_url = get_mapped_image(base_id)
    faq_items = extract_faq_items(body)
    related_guides = [g for g in get_all_guides(lang) if g.get('id') != guide_id][:6]
    featured_onsens = get_featured_onsens(lang, limit=10)
    stats = get_footer_stats(lang)

    share_ctx = _share_context(guide_id, title, lang, f"/guide/{guide_id}")

    return render_template('guide_detail.html', 
                           title=title, summary=summary, content=content_html, lang=lang, 
                           image_url=image_url, base_id=base_id, faq_items=faq_items,
                           related_guides=related_guides, featured_onsens=featured_onsens,
                           cross_site_links=cross_links_for(FAMILY_SITE_ID, lang),
                           **inject_family_context(FAMILY_SITE_ID, lang),
                           **stats, **share_ctx)

@app.route('/onsen/<onsen_id>')
def onsen_detail(onsen_id):
    md_path = os.path.join(CONTENT_DIR, f"{onsen_id}.md")
    if not os.path.exists(md_path): abort(404)
    with open(md_path, 'r', encoding='utf-8') as f:
        post = frontmatter.loads(normalize_markdown_source(f.read()))
    
    if isinstance(post.get('categories'), str):
        post['categories'] = [c.strip() for c in post['categories'].split(',')]

    # 💡 [추가] 언어 코드(_en, _ko)를 제거한 base_id 추출
    base_id = onsen_id.rsplit('_', 1)[0]
    lang = post.get('lang', 'en')

    content_html = markdown.markdown(post.content, extensions=['tables'])
    related_guides = get_all_guides(lang)[:6]
    featured_onsens = [o for o in get_featured_onsens(lang, limit=10) if o.get('id') != onsen_id][:8]
    stats = get_footer_stats(lang)
    
    share_ctx = _share_context(
        onsen_id,
        post.get("title", "OKOnsen"),
        lang,
        f"/onsen/{onsen_id}",
        base_id=base_id,
    )

    return render_template('detail.html', 
                           post=post, 
                           content=content_html, 
                           base_id=base_id, 
                           onsen_id=onsen_id,
                           lang=lang, 
                           related_guides=related_guides,
                           featured_onsens=featured_onsens,
                           cross_site_links=cross_links_for(
                               FAMILY_SITE_ID, lang, address=post.get("address")
                           ),
                           **inject_family_context(FAMILY_SITE_ID, lang),
                           **_og_image_context(base_id),
                           **stats, **share_ctx)


@app.route('/card/<onsen_id>')
def onsen_social_card(onsen_id):
    """Lightweight share landing page for X/OG crawlers."""
    md_path = os.path.join(CONTENT_DIR, f"{onsen_id}.md")
    if not os.path.exists(md_path):
        abort(404)

    with open(md_path, 'r', encoding='utf-8') as f:
        post = frontmatter.loads(normalize_markdown_source(f.read()))

    base_id = onsen_id.rsplit('_', 1)[0]
    lang = post.get('lang', 'en')
    title = post.get('title', 'OKOnsen')
    summary = post.get('summary', '')
    page_path = f"/onsen/{onsen_id}"

    return render_template(
        'social_card.html',
        lang=lang,
        title=title,
        seo_title=f"{title} - OKOnsen",
        seo_desc=summary,
        page_url=f"{SITE_URL}{page_path}",
        card_url=f"{SITE_URL}{_card_path(onsen_id)}",
        **_og_image_context(base_id),
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)