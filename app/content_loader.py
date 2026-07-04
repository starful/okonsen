"""Markdown content loading and guide listing helpers."""

from __future__ import annotations

import hashlib
import os
import re
from typing import Dict, List

import frontmatter

try:
    from .config import CORE_GUIDE_BASES, GUIDE_DIR, GUIDE_IMAGES
    from .content_new import enrich_item
except ImportError:
    from config import CORE_GUIDE_BASES, GUIDE_DIR, GUIDE_IMAGES
    from content_new import enrich_item


def get_mapped_image(base_id: str) -> str:
    idx = int(hashlib.md5(base_id.encode()).hexdigest(), 16) % len(GUIDE_IMAGES)
    return GUIDE_IMAGES[idx]


def prioritize_by_ids(items, priority_ids, id_key="id"):
    priority_set = set(priority_ids)
    priority_map = {pid: idx for idx, pid in enumerate(priority_ids)}
    prioritized = [x for x in items if x.get(id_key) in priority_set]
    remaining = [x for x in items if x.get(id_key) not in priority_set]
    prioritized.sort(key=lambda x: priority_map.get(x.get(id_key), 999))
    return prioritized + remaining


def normalize_markdown_source(raw_text: str) -> str:
    """Normalize malformed markdown sources before frontmatter parsing."""
    text = raw_text.lstrip("\ufeff")
    text = re.sub(r"^\s*yaml\s*\n(?=---\s*\n)", "", text, count=1, flags=re.IGNORECASE)
    text = re.sub(
        r"^---\s*\n\{\}\s*\n---\s*\n(?=---\s*\n)", "", text, count=1, flags=re.MULTILINE
    )
    return text


def extract_faq_items(body: str, limit: int = 6) -> List[Dict[str, str]]:
    """Extract Q/A pairs from markdown body for FAQPage schema."""
    pattern = re.compile(
        r"\*\*Q\d*[:：]\s*(.*?)\*\*\s*\nA[:：]\s*(.*?)(?=\n\s*\*\*Q\d*[:：]|\Z)",
        re.DOTALL,
    )
    faqs = []
    for q, a in pattern.findall(body):
        q_clean = re.sub(r"\s+", " ", q).strip()
        a_clean = re.sub(r"\s+", " ", a).strip()
        if q_clean and a_clean:
            faqs.append({"question": q_clean, "answer": a_clean})
        if len(faqs) >= limit:
            break
    return faqs


def get_all_guides(lang: str) -> list:
    guides = []
    if not os.path.exists(GUIDE_DIR):
        return guides

    raw_guides = []
    for f in os.listdir(GUIDE_DIR):
        if f.endswith(f"_{lang}.md"):
            path = os.path.join(GUIDE_DIR, f)
            base_id = f.replace(f"_{lang}.md", "")
            try:
                with open(path, "r", encoding="utf-8") as file:
                    raw_text = normalize_markdown_source(file.read())
                    post = frontmatter.loads(raw_text)
                    title = post.get("title")
                    summary = post.get("summary")

                    if not title or title == "None":
                        title_match = re.search(r'title:\s*"(.*?)"', raw_text)
                        title = title_match.group(1) if title_match else "Travel Guide"
                    if not summary or summary == "None":
                        summary_match = re.search(r'summary:\s*"(.*?)"', raw_text)
                        summary = (
                            summary_match.group(1)
                            if summary_match
                            else post.content[:150].replace("\n", " ")
                        )

                    raw_guides.append(
                        {
                            "id": f.replace(".md", ""),
                            "base_id": base_id,
                            "title": title,
                            "summary": summary,
                            "date": str(post.get("date", "2024-01-01")),
                        }
                    )
            except Exception:
                continue

    sorted_guides = sorted(raw_guides, key=lambda x: (x["date"], x["id"]), reverse=True)

    last_img_idx = -1
    for item in sorted_guides:
        img_idx = int(hashlib.md5(item["base_id"].encode()).hexdigest(), 16) % len(
            GUIDE_IMAGES
        )
        if img_idx == last_img_idx:
            img_idx = (img_idx + 1) % len(GUIDE_IMAGES)

        item["image"] = GUIDE_IMAGES[img_idx]
        last_img_idx = img_idx
        guides.append(enrich_item({**item, "published": item.get("date", "")}))

    return guides


def get_priority_guides(lang: str, limit: int = 8) -> list:
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
