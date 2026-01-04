# ⛩️ JinjaMap - Your Interactive Guide to Japan's Sacred Power Spots

An interactive web application designed to help travelers discover and explore Japan's rich spiritual heritage. Find your fortune by filtering shrines based on themes like Wealth, Love, and Success.

🔗 **Live Demo:** [https://jinjamap.com](https://jinjamap.com)

---

## ✨ Features

*   **Interactive Google Map**: Shrines are plotted on a dynamic map with auto-adjusting views to show all locations at a glance.
*   **Theme-based Filtering**: Easily find shrines that match your wishes (e.g., Wealth, Love, Health, Success).
*   **High-Performance Architecture**:
    *   **In-Memory Caching**: Server responses are optimized to serve data instantly from memory.
    *   **Static Pre-generation**: Site maps and data JSONs are built at deployment time, reducing server load.
    *   **CDN Integration**: Images are delivered via Cloudinary for global speed.
*   **Detailed Shrine Guides**: Each shrine has a dedicated page with history, deity info, access details, and nearby onsen recommendations.
*   **Hybrid Content Strategy**: Combines AI-generated base content with high-quality, manually curated "Anchor" articles featuring real experiences and photos.
*   **Intelligent Image Optimization**: Custom scripts automatically resize and compress images to optimal web standards (under 100KB).
*   **Omikuji Fortune Game**: A fun, interactive feature to draw a daily fortune slip.

---

## 🛠️ Tech Stack & Architecture

This project leverages a modern "Jamstack-like" architecture within a Flask environment for maximum performance and ease of maintenance.

*   **Backend**: Python 3.10, Flask (with `flask-compress`)
*   **Frontend**: Vanilla JavaScript (ESM), HTML5, CSS3, Google Maps API
*   **Data & Content**: Markdown with YAML Frontmatter -> Compiled to JSON.
*   **Automation**:
    *   **Generation**: Google Gemini API for drafting articles.
    *   **Optimization**: Pillow (PIL) for smart image compression.
    *   **Build**: Custom Python script (`build_data.py`) for static asset generation.
*   **Infrastructure**: Docker, Google Cloud Run, Cloud Build.

---

## 📂 Project Structure

```text
jinjaMap/
├── app/
│   ├── content/                 # Source Data (Markdown files)
│   │   └── images/              # Optimized Images
│   ├── static/                  # Assets & Generated Artifacts
│   │   ├── json/                # shrines_data.json (Generated)
│   │   └── ...
│   ├── templates/               # HTML Templates
│   └── __init__.py              # Flask App (Memory Caching Implemented)
│
├── script/
│   ├── build_data.py            # [Core] Compiles MD to JSON/XML
│   ├── jinja_generator.py       # AI Content Generator
│   └── compress_images_target.py # Smart Image Optimizer (<100KB)
│
├── Dockerfile                   # Docker Config (Runs build_data.py)
├── cloudbuild.yaml              # CI/CD Configuration
└── requirements.txt             # Python Dependencies
```

---

## 🚀 Development Workflow

### 1. Adding New Content
You don't need a database. Just add a Markdown file!

1.  **Generate or Write**: Use `script/jinja_generator.py` for drafts or write manually.
2.  **Add Images**: Place images in `app/content/images`.
3.  **Optimize Images**: Run the compression script.
    ```bash
    python script/compress_images_target.py
    ```

### 2. Local Testing
To see changes locally, you must run the build script to update the JSON data.

```bash
# 1. Build Data (Generates app/static/json/shrines_data.json)
python script/build_data.py

# 2. Run Server
python app/__init__.py
```

### 3. Deployment
Deployment is fully automated via **Google Cloud Build**.

```bash
# Deploy to Cloud Run (Triggers build_data.py automatically)
gcloud builds submit
```

The `Dockerfile` ensures that `script/build_data.py` runs during the container build process, "baking" the latest data into the image.

---

## 📈 SEO & Trust Strategy

*   **E-E-A-T Focused**: Prioritizes "Experience" by featuring high-quality articles with original photography and personal stories.
*   **Technical SEO**:
    *   Automatic `sitemap.xml` generation.
    *   `ads.txt` support.
    *   Meta tags and Open Graph support for social sharing.
    *   DNS prefetching and preconnects for faster resource loading.
*   **Trust Signals**: dedicated `About` and `Contact` pages to establish site credibility.

---

## 🛡️ License

This project is open-source and available under the [MIT License](LICENSE).
