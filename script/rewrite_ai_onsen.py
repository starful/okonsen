#!/usr/bin/env python3
"""AI rewrite for OKOnsen — long-form ~7,000 chars, preserves frontmatter facts."""

from __future__ import annotations

import argparse
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import frontmatter
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

CONTENT = ROOT / "app" / "content"
GUIDES = CONTENT / "guides"
GCS_IMAGE_BASE = "https://storage.googleapis.com/ok-project-assets/okonsen"

load_dotenv(ROOT / ".env")

OLD_ONSEN_MARKERS = ("**Overview:**", "Screenshot the Maps")
AI_ONSEN_MARKERS = ("## Introduction", "## 소개", "## History", "## 역사", "## Deep Dive", "## 온천")
OLD_GUIDE_MARKERS = ("## Quick checklist", "## 체크리스트")
BILINGUAL_HEADER = re.compile(r"^## .+ / [\uac00-\ud7a3]", re.M)

_thread_local = threading.local()


def base_slug(stem: str) -> str:
    if stem.endswith("_en") or stem.endswith("_ko"):
        return stem.rsplit("_", 1)[0]
    return stem


def lang_from_stem(stem: str) -> str:
    return "ko" if stem.endswith("_ko") else "en"


def clean_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    return text.replace("```markdown", "").replace("```", "").strip()


def get_client(api_key: str):
    if getattr(_thread_local, "client", None) is None:
        from google import genai

        _thread_local.client = genai.Client(api_key=api_key)
    return _thread_local.client


def call_gemini(api_key: str, prompt: str) -> str:
    client = get_client(api_key)
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return clean_response(response.text)


def parse_ai_output(raw: str, fallback_meta: dict) -> tuple[dict, str]:
    raw = clean_response(raw)
    meta = dict(fallback_meta)
    if not raw.startswith("---"):
        return meta, raw

    parts = raw.split("---", 2)
    body = parts[2].strip() if len(parts) >= 3 else ""
    try:
        post = frontmatter.loads(raw)
        meta.update({k: v for k, v in post.metadata.items() if v is not None and v != ""})
        body = post.content.strip() or body
    except Exception:
        if len(parts) >= 2:
            try:
                loaded = yaml.safe_load(parts[1]) or {}
                if isinstance(loaded, dict):
                    meta.update(loaded)
            except Exception:
                pass
    return meta, body


def strip_leading_yaml_in_body(body: str) -> str:
    """Remove accidental duplicate YAML block at start of markdown body."""
    text = body.strip()
    while text:
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3 and "lang:" in parts[1]:
                text = parts[2].strip()
                continue
            break
        if re.match(r"^lang:\s", text):
            end = re.search(r"\n---\s*\n", text)
            if end:
                text = text[end.end() :].strip()
                continue
            break
        break
    return text


def dump_meta(meta: dict) -> str:
    class Dumper(yaml.SafeDumper):
        pass

    def represent_str(dumper, data):
        if "\n" in data:
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        if any(c in data for c in ":{}[]#&*!|>'\"%@`"):
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    Dumper.add_representer(str, represent_str)
    return yaml.dump(meta, Dumper=Dumper, allow_unicode=True, sort_keys=False).strip()


def merge_onsen_meta(old: dict, new: dict) -> dict:
    keep = ("address", "lat", "lng", "categories", "date", "thumbnail", "agoda", "lang", "shop_name")
    merged = dict(old)
    for k, v in new.items():
        if k in keep and old.get(k) not in (None, ""):
            merged[k] = old[k]
        elif v is not None and v != "":
            merged[k] = v
    if not merged.get("thumbnail") and old.get("thumbnail"):
        merged["thumbnail"] = old["thumbnail"]
    if not merged.get("date"):
        merged["date"] = old.get("date") or datetime.now().strftime("%Y-%m-%d")
    return merged


def onsen_prompt(meta: dict, lang: str, base: str) -> str:
    lang_name = "Korean" if lang == "ko" else "English"
    cats = ", ".join(str(c) for c in (meta.get("categories") or []))
    title_hint = meta.get("title") or base.replace("_", " ")
    return f"""You are an elite Japan onsen/ryokan travel journalist. Write in {lang_name} ONLY.

Property: {meta.get('shop_name') or title_hint}
Address: {meta.get('address')}
Categories: {cats}
Coordinates: {meta.get('lat')}, {meta.get('lng')}

Length: 6,500–8,000 characters in the markdown body (excluding frontmatter).

Rules:
- Use ## and ### headings only (never # H1 in body).
- Do NOT use bilingual headings (no "English / Korean" in one heading).
- Write entirely in {lang_name}; no mixed-language footers.
- Do NOT invent exact hours, prices, or policies as facts — use "typically" or "check when booking".
- No clichés ("embark on a journey", "delve into").
- Rich detail on baths, water type, rooms, kaiseki, local area, access, tattoo policy if relevant.

Sections (## in {lang_name}):
- Introduction / 소개
- History & tradition / 역사와 전통
- Baths & water / 온천과 수질
- Rooms & architecture / 객실과 건축
- Dining / 식사 (kaiseki)
- Local area / 주변 관광
- Practical tips / 실용 정보
- Access / 오시는 길

Output YAML frontmatter then body. Quote all YAML string values with double quotes.
Preserve: lang, lat, lng, address, date, thumbnail, agoda, categories
Update: title, summary

---
lang: {lang}
title: "..."
lat: {meta.get('lat')}
lng: {meta.get('lng')}
categories: [...]
thumbnail: "{meta.get('thumbnail') or f'{GCS_IMAGE_BASE}/{base}.jpg'}"
address: "{meta.get('address', '')}"
date: "{meta.get('date') or datetime.now().strftime('%Y-%m-%d')}"
agoda: "{meta.get('agoda', '')}"
summary: "..."
---

(body markdown, no code fences)
"""


def guide_prompt(meta: dict, lang: str, base: str) -> str:
    lang_name = "Korean" if lang == "ko" else "English"
    topic = meta.get("title") or base.replace("_", " ").title()
    return f"""Write an exhaustive Japan onsen travel guide in {lang_name} ONLY.

Topic: {topic}
Slug: {base}
Length: 5,500–7,500 characters in the body.

Rules:
- Use ## and ### headings; no # in body.
- No bilingual headings or mixed-language footers.
- Specific, useful facts — not generic filler repeated on every guide.
- Do NOT invent restaurant/ryokan names or exact policies unless widely known.

End with one line linking to / and /guides (language-appropriate):
- EN: [Find onsen on the OKOnsen map](/) · [More guides](/guides)
- KO: [OKOnsen 지도에서 온천 찾기](/) · [다른 가이드](/guides)

Output YAML (quoted strings) then markdown body.
---
lang: {lang}
title: "..."
date: "{meta.get('date') or datetime.now().strftime('%Y-%m-%d')}"
summary: "..."
seo_title: "... | OKOnsen"
seo_description: "..."
---
"""


def write_file(path: Path, meta: dict, body: str) -> None:
    from fix_mixed_language import fix_en_text, fix_ko_text

    lang = lang_from_stem(path.stem)
    is_guide = "guides" in path.parts
    body = strip_leading_yaml_in_body(body)
    text = f"---\n{dump_meta(meta)}\n---\n\n{body.strip()}\n"
    text = fix_en_text(text, is_guide=is_guide) if lang == "en" else fix_ko_text(text, is_guide=is_guide)
    path.write_text(text, encoding="utf-8")


def hangul_in(text: str) -> bool:
    return bool(re.search(r"[\uac00-\ud7a3]", text))


def rewrite_onsen(path: Path, api_key: str, force: bool) -> str:
    raw = path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw)
    meta = dict(post.metadata)
    lang = lang_from_stem(path.stem)
    base = base_slug(path.stem)

    if not force and len(post.content) >= 5500 and not BILINGUAL_HEADER.search(post.content):
        if lang == "en" and not hangul_in(post.content):
            return "skip"
        if lang == "ko":
            return "skip"

    prompt = onsen_prompt(meta, lang, base)
    out = call_gemini(api_key, prompt)
    new_meta, body = parse_ai_output(out, meta)
    new_meta = merge_onsen_meta(meta, new_meta)
    new_meta["lang"] = lang
    write_file(path, new_meta, body)
    return "onsen"


def rewrite_guide(path: Path, api_key: str, force: bool) -> str:
    raw = path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw)
    meta = dict(post.metadata)
    lang = lang_from_stem(path.stem)
    base = base_slug(path.stem)

    if not force and len(post.content) >= 4500 and not any(m in post.content for m in OLD_GUIDE_MARKERS):
        if lang == "en" and not hangul_in(post.content):
            return "skip"

    prompt = guide_prompt(meta, lang, base)
    out = call_gemini(api_key, prompt)
    new_meta, body = parse_ai_output(out, meta)
    new_meta["lang"] = lang
    if not new_meta.get("date"):
        new_meta["date"] = meta.get("date") or datetime.now().strftime("%Y-%m-%d")
    write_file(path, new_meta, body)
    return "guide"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--onsen-only", action="store_true")
    parser.add_argument("--guides-only", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and not args.dry_run:
        print("❌ GEMINI_API_KEY missing")
        return 1

    tasks: list[tuple[str, Path]] = []
    if not args.guides_only:
        for p in sorted(CONTENT.glob("*.md")):
            tasks.append(("onsen", p))
    if not args.onsen_only:
        for p in sorted(GUIDES.glob("*.md")):
            tasks.append(("guide", p))

    print(f"🚀 Rewrite queue: {len(tasks)} files (workers={args.workers})", flush=True)
    counts: dict[str, int] = {}
    errors: list[str] = []

    def run(item):
        kind, path = item
        if args.dry_run:
            return kind, path.name, "would"
        try:
            if kind == "onsen":
                r = rewrite_onsen(path, api_key, args.force)
            else:
                r = rewrite_guide(path, api_key, args.force)
            return kind, path.name, r
        except Exception as e:
            return kind, path.name, f"error:{e}"

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(run, t) for t in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            kind, name, result = fut.result()
            if str(result).startswith("error:"):
                errors.append(f"{name}: {result[6:]}")
                print(f"⚠️  [{i}/{len(tasks)}] {name} — {result[6:]}", flush=True)
            elif result not in ("skip", "would"):
                counts[result] = counts.get(result, 0) + 1
                print(f"✅ [{i}/{len(tasks)}] {name} ({result})", flush=True)

    print("Summary:", counts, flush=True)
    if errors:
        print(f"Errors: {len(errors)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
