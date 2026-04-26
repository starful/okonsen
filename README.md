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
python3 app/__init__.py
```

Open `http://localhost:8080`.

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

Do not rely on `.env` in Cloud Run. Inject runtime variables during deployment.

`cloudbuild.yaml` supports these substitutions:

- `_GOOGLE_MAPS_API_KEY`
- `_GEMINI_API_KEY`

Example:

```bash
gcloud builds submit \
  --substitutions=_GOOGLE_MAPS_API_KEY="your_maps_key",_GEMINI_API_KEY="your_gemini_key"
```

The deploy step applies them to Cloud Run via `--set-env-vars`.

## Secret Safety

- `.env` and `.env.*` are excluded from Docker/Cloud Build context.
- Added `.dockerignore` and `.gcloudignore` to prevent accidental secret uploads.

## Project Structure

```text
okonsen/
├── app/
│   ├── __init__.py
│   ├── content/
│   ├── static/
│   │   ├── css/
│   │   ├── images/
│   │   ├── js/
│   │   │   └── main.js
│   │   └── json/
│   └── templates/
├── script/
├── deploy.sh
├── Dockerfile
├── cloudbuild.yaml
└── requirements.txt
```

## Notes

- Legacy/unused JS modules were removed from `app/static/js` to avoid mixed domain logic.
- Keep generated content and static assets versioned carefully when using `--with-git`.
