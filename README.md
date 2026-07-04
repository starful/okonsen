# OKOnsen

Flask-based web service for discovering onsen/ryokan with multilingual content, map filtering, and generated markdown-driven data.

Live: [https://okonsen.net](https://okonsen.net)

## Highlights

- Server-rendered pages with Flask + Jinja templates.
- Frontend map/list UI in `app/static/js/main.js`.
- Content source in markdown (`app/content`) compiled into JSON.
- No runtime DB dependency for core read paths.
- Optional automation for content generation, image processing, and deployment.

## Stack

- Backend: Python, Flask, flask-compress, Gunicorn
- Frontend: HTML/CSS, vanilla JavaScript (ES modules), Google Maps JS API
- Content/Data: Markdown + frontmatter -> `app/static/json/onsen_data.json`
- Infra: Docker, Cloud Build, Cloud Run

## Required Environment Variables

Create `.env` (or export in your shell):

```env
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_browser_key
```

`GOOGLE_MAPS_API_KEY` is injected into `index.html` from Flask. No map key is hardcoded in templates.

## Local Run

```bash
pip install -r requirements.txt
python3 script/build_data.py
python3 -m flask --app app run --port 8080
# or: python3 app/__init__.py
```

Open `http://localhost:8080`.

## Tests

```bash
pip install -r requirements-dev.txt
python3 script/build_data.py
pytest tests/ -v
```

Cloud Build runs `pytest` before the Docker image is built (`cloudbuild.yaml`).

## Build/Generation Scripts

- `script/guide_generator.py`: generates guide markdown
- `script/onsen_generator.py`: generates onsen markdown
- `script/fetch_images.py`: fetches images
- `script/optimize_images.py`: compresses/resizes images
- `script/build_data.py`: builds JSON + sitemap

## Deployment Script

`deploy.sh` is now step-oriented and does not force all operations every time.

### Modes

```bash
./deploy.sh --full
./deploy.sh --content-only
./deploy.sh --images-only
./deploy.sh --build-only
./deploy.sh --deploy-only
```

### Optional flags

```bash
./deploy.sh --full --with-git --with-deploy
```

- `--with-git`: `git add/commit/push`
- `--with-deploy`: runs `gcloud builds submit`

### Optional env overrides

```bash
GCS_BUCKET=gs://your-bucket/path GCP_PROJECT_ID=your-project ./deploy.sh --images-only
```

## Cloud Run Deployment (Recommended)

Do not rely on `.env` in Cloud Run. Secrets are injected at deploy time via Cloud Run secret bindings.

`cloudbuild.yaml` pipeline:

1. Run pytest
2. Build and push Docker image
3. Deploy to Cloud Run with secrets (`OKONSEN_GOOGLE_MAPS_API_KEY`, `GEMINI_API_KEY`)

```bash
./deploy.sh --deploy-only
# or
gcloud builds submit --project starful-258005
```

## Secret Safety

- `.env` and `.env.*` are excluded from Docker/Cloud Build context.
- Added `.dockerignore` and `.gcloudignore` to prevent accidental secret uploads.

## Project Structure

```text
okonsen/
├── app/
│   ├── __init__.py          # Flask app factory & blueprint wiring
│   ├── config.py            # paths, env, constants
│   ├── data_cache.py        # onsen JSON cache
│   ├── content_loader.py    # guide/markdown helpers
│   ├── images.py            # GCS URLs, OG/social images
│   ├── seo.py               # URL normalization, share meta
│   ├── reactions.py         # Firestore reactions API
│   ├── family_sites.py      # cross-site footer links
│   ├── content_new.py       # "new" badge enrichment
│   ├── routes/
│   │   ├── static_routes.py # sitemap, robots, images, about
│   │   ├── pages.py         # home, guide hub
│   │   ├── guides.py        # guide detail
│   │   └── onsen.py         # onsen detail, map API, social card
│   ├── content/             # markdown source
│   ├── static/
│   │   ├── css/
│   │   ├── images/
│   │   ├── js/main.js
│   │   └── json/onsen_data.json
│   └── templates/
├── tests/
│   ├── test_routes.py
│   ├── test_seo.py
│   └── test_reactions.py
├── script/
├── deploy.sh
├── Dockerfile
├── cloudbuild.yaml
├── requirements.txt
└── requirements-dev.txt
```

## Notes

- Flask routes are split into blueprints under `app/routes/`; behavior and URLs are unchanged from the monolithic layout.
- Legacy/unused JS modules were removed from `app/static/js` to avoid mixed domain logic.
- Keep generated content and static assets versioned carefully when using `--with-git`.
