"""Application constants, paths, and environment configuration."""

import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

SITE_URL = os.environ.get("SITE_URL", "https://okonsen.net").rstrip("/")
GCS_ASSET_PREFIX = "okonsen"
FAMILY_SITE_ID = "okonsen"

GOOGLE_MAPS_API_KEY = (
    os.environ.get("GOOGLE_MAPS_API_KEY")
    or os.environ.get("GOOGLE_PLACES_API_KEY")
    or ""
).strip()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_FILE = os.path.join(STATIC_DIR, "json", "onsen_data.json")
CONTENT_DIR = os.path.join(BASE_DIR, "content")
GUIDE_DIR = os.path.join(CONTENT_DIR, "guides")

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

CATEGORY_MAPPING = {
    "가족탕": "Private Bath",
    "타투 허용": "Tattoo OK",
    "절경": "Great View",
    "고급 료칸": "Luxury",
    "고급": "Luxury",
    "로컬": "Local",
}

GUIDE_IMAGES = [
    "https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=1000",
    "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?q=80&w=1000",
    "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?q=80&w=1000",
    "https://images.unsplash.com/photo-1526481280693-3bfa7568e0f3?q=80&w=1000",
    "https://images.unsplash.com/photo-1545569341-9eb8b30979d9?q=80&w=1000",
    "https://images.unsplash.com/photo-1528360983277-13d401cdc186?q=80&w=1000",
    "https://images.unsplash.com/photo-1580822184713-fc5400e7fe10?q=80&w=1000",
    "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?q=80&w=1000",
    "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?q=80&w=1000",
    "https://images.unsplash.com/photo-1518709766631-a6a7f45921c3?q=80&w=1000",
    "https://images.unsplash.com/photo-1596395819057-e37f55a8516b?q=80&w=1000",
    "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?q=80&w=1000",
    "https://images.unsplash.com/photo-1478436127897-769e1b3f0f36?q=80&w=1000",
    "https://images.unsplash.com/photo-1526481280693-3bfa7568e0f3?q=80&w=1000",
    "https://images.unsplash.com/photo-1524230572899-a752b3835840?q=80&w=1000",
    "https://images.unsplash.com/photo-1576092768241-dec231879fc3?q=80&w=1000",
]
