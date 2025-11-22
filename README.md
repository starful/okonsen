# ⛩️ JinjaMap (Tokyo Shrine Explorer)

**JinjaMap** is a web application that maps major shrines in Tokyo, dynamically syncing with a Hatena Blog to discover them based on specific wishes and themes. It utilizes the Google Maps API for visualization and Python Flask for backend processing.

## ✨ Features

*   **Hatena Blog Integration**: Automatically fetches blog posts, extracts addresses, and maps them using the Hatena AtomPub API.
*   **Google Maps Integration**: Visualizes the locations of shrines across Tokyo with interactive markers.
*   **Theme-Based Filtering**: Filter shrines by specific purposes based on blog categories:
    *   💰 **Wealth** (Business success, financial luck)
    *   ❤️ **Love** (Relationships, marriage)
    *   💊 **Health** (Longevity, healing)
    *   🎓 **Study** (Academic success)
    *   And more (Safety, Family, Success, Art, Relax, History).
*   **Responsive Design**: Optimized for both desktop and mobile devices.
*   **Serverless Deployment**: Hosted using Docker and Python Flask on Google Cloud Run.

## 🛠️ Tech Stack

*   **Backend**: Python 3.9, Flask, Gunicorn
*   **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
*   **API**: Google Maps JavaScript API, Hatena Blog AtomPub API
*   **Infrastructure**: Docker, Google Cloud Run, Cloud Build

## 📂 Project Structure

```text
jinjaMap/
├── app.py            # Flask application entry point (API & Server)
├── hatena_client.py  # Logic to fetch and parse Hatena Blog data
├── requirements.txt  # Python dependencies
├── Dockerfile        # Python environment configuration
├── cloudbuild.yaml   # CI/CD config with variable substitution
├── index.html        # Main frontend template
└── assets/           # Static files
    ├── css/          # Stylesheets
    ├── js/           # Map logic (fetches data from Flask API)
    └── images/       # Assets
```

## 🚀 Deployment Guide (Google Cloud Run)

This project is deployed to Google Cloud Run. You can choose between **Automated Deployment** (via Cloud Build) or **Manual Deployment**.

### 1. Prerequisites
Ensure you have the Google Cloud SDK (`gcloud`) installed and authenticated.

```bash
# Set your project ID
gcloud config set project starful-258005
```

### 2. Method A: Automated Build & Deploy (Recommended)
This method uses `cloudbuild.yaml` to build the Docker image and deploy it to Cloud Run in a single command. It also safely handles your API credentials.

**Run the following command:**
(Replace `YOUR_...` with your actual Hatena Blog credentials)

```bash
gcloud builds submit \
    --substitutions=_HATENA_USERNAME="YOUR_HATENA_ID",_HATENA_BLOG_ID="blog.jinjamap.com",_HATENA_API_KEY="YOUR_API_KEY"
```

*   **Note**: This command executes the steps defined in `cloudbuild.yaml`:
    1.  Builds the Docker image.
    2.  Pushes it to the Artifact Registry.
    3.  **Deploys** the service (`jinjamap`) to Cloud Run automatically.

### 3. Method B: Manual Deployment
If you prefer to build and deploy separately, or need to redeploy an existing image without rebuilding.

**Step 1: Build & Push Image**
```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/starful-258005/jinjamap-repo/jinjamap
```

**Step 2: Deploy to Cloud Run**
```bash
gcloud run deploy jinjamap \
  --image us-central1-docker.pkg.dev/starful-258005/jinjamap-repo/jinjamap \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars=HATENA_USERNAME="YOUR_HATENA_ID",HATENA_BLOG_ID="blog.jinjamap.com",HATENA_API_KEY="YOUR_API_KEY"
```

## ⚠️ API Configuration

### Google Maps API
For the map to work, ensure your `index.html` contains a valid API key with **HTTP Referrer restrictions** configured in Google Cloud Console:
*   `https://jinjamap-*.run.app/*`
*   `https://jinjamap.com/*`

### Hatena Blog API
The backend (`hatena_client.py`) connects to Hatena. Ensure your blog posts have:
1.  **Categories** set (e.g., "재물", "연애").
2.  **Address** in the content body (e.g., `주소: 도쿄도...` or `Address: Tokyo...`) for Geocoding.

## 📝 License

This project is for educational and portfolio purposes.