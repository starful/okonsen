"""Generation guards: allow same topics, reject thin/duplicate/low-quality output.

Policy (GSC cleanup 2026-07):
- Same onsen/guide topic may be (re)generated.
- Near-duplicate guide IDs must not be created alongside their canonical.
- Every write must pass a quality gate (length, frontmatter, language fit).
"""

from __future__ import annotations

import re
from pathlib import Path

# Near-identical guide topics → keep only the canonical id.
GUIDE_DUPLICATE_OF: dict[str, str] = {
    "beppu_eight_hells_tour": "beppu_hell_tour_guide",
}

ONSEN_MIN_CHARS = 4500
GUIDE_MIN_CHARS = 4000
# Sibling locale fill (one lang already live) uses a higher bar.
SIBLING_FILL_MIN_CHARS = 5500

HANGUL_RE = re.compile(r"[\uac00-\ud7a3]")
FM_SPLIT = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.S)


def base_slug(stem: str) -> str:
    if stem.endswith("_en") or stem.endswith("_ko"):
        return stem.rsplit("_", 1)[0]
    return stem


def lang_from_stem(stem: str) -> str:
    return "ko" if stem.endswith("_ko") else "en"


def strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-z]*\n", "", text, flags=re.I)
    text = re.sub(r"\n```$", "", text)
    return text.replace("```markdown", "").replace("```", "").strip()


def parse_frontmatter_body(raw: str) -> tuple[dict[str, str], str]:
    raw = strip_code_fences(raw)
    m = FM_SPLIT.match(raw)
    if not m:
        return {}, raw
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, m.group(2).strip()


def hangul_ratio(text: str) -> float:
    if not text:
        return 0.0
    hangul = len(HANGUL_RE.findall(text))
    return hangul / max(len(text), 1)


def duplicate_guide_reason(base_id: str, guide_dir: str | Path) -> str | None:
    """Return skip reason if base_id is a blocked duplicate of an existing/canonical guide."""
    base_id = (base_id or "").strip()
    if not base_id:
        return "missing_id"
    canonical = GUIDE_DUPLICATE_OF.get(base_id)
    if not canonical:
        return None
    guide_dir = Path(guide_dir)
    if any(guide_dir.glob(f"{canonical}_*.md")):
        return f"duplicate_of:{canonical}"
    # Even if canonical is not on disk yet, never generate the alias id.
    return f"alias_blocked:{canonical}"


def min_chars_for(*, kind: str, sibling_exists: bool) -> int:
    if sibling_exists:
        return SIBLING_FILL_MIN_CHARS
    return ONSEN_MIN_CHARS if kind == "onsen" else GUIDE_MIN_CHARS


def validate_generated_markdown(
    raw: str,
    *,
    kind: str,
    lang: str,
    sibling_exists: bool = False,
) -> tuple[bool, list[str]]:
    """Quality gate before writing. Same topic OK; thin/wrong-lang output is not."""
    errors: list[str] = []
    meta, body = parse_frontmatter_body(raw)
    min_chars = min_chars_for(kind=kind, sibling_exists=sibling_exists)

    if not meta:
        errors.append("missing_frontmatter")
    else:
        required = ["lang", "title", "summary", "date"]
        if kind == "onsen":
            required.extend(["lat", "lng", "address", "categories", "thumbnail"])
        for key in required:
            if not str(meta.get(key, "")).strip():
                errors.append(f"missing_meta:{key}")
        meta_lang = str(meta.get("lang", "")).strip().lower()
        if meta_lang and meta_lang != lang:
            errors.append(f"lang_mismatch_meta:{meta_lang}!={lang}")

    if len(body) < min_chars:
        errors.append(f"too_short:{len(body)}<{min_chars}")

    ratio = hangul_ratio(body)
    if lang == "ko" and ratio < 0.08:
        errors.append(f"ko_too_little_hangul:{ratio:.3f}")
    if lang == "en" and ratio > 0.12:
        errors.append(f"en_too_much_hangul:{ratio:.3f}")

    heading_count = len(re.findall(r"^##\s+\S", body, re.M))
    if heading_count < 3:
        errors.append(f"too_few_sections:{heading_count}")

    return (len(errors) == 0), errors


def sibling_path(content_dir: str | Path, base: str, lang: str) -> Path:
    other = "ko" if lang == "en" else "en"
    return Path(content_dir) / f"{base}_{other}.md"


def sibling_exists(content_dir: str | Path, base: str, lang: str) -> bool:
    return sibling_path(content_dir, base, lang).is_file()
