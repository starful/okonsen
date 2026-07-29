# GSC URL Inspection — Priority Indexing List

After deploy, request indexing for these URLs in Google Search Console (URL inspection → Request indexing).

Do **not** request indexing for:
- Any URL in `CONTENT_GONE_REDIRECTS` / `GSC_404_REDIRECTS` (`app/seo.py`)
- `/card/*` (noindex + robots Disallow)
- `/onsen/...?lang=` or `/guide/...?lang=` (301-stripped)

## Core guides (EN)
- https://okonsen.net/guide/tattoo_friendly_onsen_list_en
- https://okonsen.net/guide/kurokawa_hidden_gems_en
- https://okonsen.net/guide/tattoo_friendly_master_list_en
- https://okonsen.net/guide/onsen_etiquette_basics_en
- https://okonsen.net/guide/onsen_etiquette_guide_en
- https://okonsen.net/guide/hakone_area_deep_dive_en

## Core guides (KO)
- https://okonsen.net/guide/tattoo_friendly_onsen_list_ko
- https://okonsen.net/guide/tattoo_friendly_master_list_ko
- https://okonsen.net/guide/onsen_etiquette_basics_ko

## Core onsens
- https://okonsen.net/onsen/kusatsu_onsen_ryokan_yoshinoya_en
- https://okonsen.net/onsen/kurokawa_onsen_hozantei_en
- https://okonsen.net/onsen/the_prince_hakone_lake_ashinoko_en
- https://okonsen.net/onsen/yufuin_onsen_yufuin-so_en

## Hubs
- https://okonsen.net/
- https://okonsen.net/?lang=ko
- https://okonsen.net/guides
- https://okonsen.net/guides?lang=ko

## Sitemap
- Resubmit: https://okonsen.net/sitemap.xml

## After deploy (GSC)
1. Resubmit sitemap
2. On redirect / 404 reasons → Start validation
3. Spot-check a former 404 URL (should 301) and a surviving onsen (200, no bad hreflang)
