"""Shared SEO priority URL sets (GSC high-impression targets)."""

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
    "kurokawa_onsen_hozantei_en",
    "the_prince_hakone_lake_ashinoko_en",
    "yufuin_onsen_yufuin-so_en",
    "yufuin_onsen_yufuin-so_ko",
]


def guide_id(base: str, lang: str) -> str:
    return f"{base}_{lang}"


def prioritize_by_ids(items, priority_ids, id_key="id"):
    priority_set = set(priority_ids)
    priority_map = {pid: idx for idx, pid in enumerate(priority_ids)}
    prioritized = [x for x in items if x.get(id_key) in priority_set]
    remaining = [x for x in items if x.get(id_key) not in priority_set]
    prioritized.sort(key=lambda x: priority_map.get(x.get(id_key), 999))
    return prioritized + remaining
