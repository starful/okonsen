# ⛩️ JinjaMap (Tokyo Shrine Explorer)

**JinjaMap** is a web application that maps major shrines in Tokyo, allowing users to discover them based on specific wishes and themes. It utilizes the Google Maps API to provide an interactive experience.

## ✨ Features

*   **Google Maps Integration**: Visualizes the locations of shrines across Tokyo.
*   **Theme-Based Filtering**: Filter shrines by specific purposes, such as:
    *   💰 **Wealth** (Business success, financial luck)
    *   ❤️ **Love** (Relationships, marriage)
    *   💊 **Health** (Longevity, healing)
    *   🎓 **Study** (Academic success)
    *   And more (Safety, Family, Success, Art, Relax, History).
*   **Responsive Design**: Optimized for both desktop and mobile devices.
*   **Containerized Deployment**: Hosted using Docker and Nginx on Google Cloud Run.

## 🛠️ Tech Stack

*   **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
*   **API**: Google Maps JavaScript API
*   **Infrastructure**: Docker, Nginx
*   **Cloud**: Google Cloud Platform (Cloud Run, Artifact Registry, Cloud Build)

## 📂 Project Structure

```text
JinjaMap/
├── index.html        # Main entry point (Google Maps loader)
├── style.css         # Application styling
├── map.js            # Map initialization and marker logic
├── JinjaMapLogo.png  # Logo asset
├── Dockerfile        # Nginx-based container configuration
├── cloudbuild.yaml   # Google Cloud Build configuration
└── README.md         # Project documentation
```

## 🚀 Deployment Guide (Google Cloud Run)

This project is deployed to Google Cloud Run. Follow these steps to deploy updates.

### 1. Prerequisites
Ensure you have the Google Cloud SDK (`gcloud`) installed and authenticated.

```bash
# Set your project ID
gcloud config set project starful-258005
```

### 2. Docker Configuration
The project uses a lightweight Nginx image.
**Dockerfile:**
```dockerfile
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
```

### 3. Deploying to Cloud Run

You can deploy using the following commands in your terminal:

**Step 1: Build the container image**
Uploads the build to the Artifact Registry.
```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/starful-258005/jinjamap-repo/jinjamap
```

**Step 2: Deploy to Cloud Run**
Deploys the image to a live server in the `us-central1` region.
```bash
gcloud run deploy jinjamap \
  --image us-central1-docker.pkg.dev/starful-258005/jinjamap-repo/jinjamap \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 80
```

## ⚠️ Google Maps API Configuration

For the map to work correctly on the deployed site:

1.  **Update `index.html`**: Ensure the script tag contains your valid API key.
    ```html
    <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY..."></script>
    ```
2.  **Google Cloud Console Settings**:
    *   Go to **APIs & Services > Credentials**.
    *   Select your API Key.
    *   Under **Application restrictions (HTTP referrers)**, add your Cloud Run URL:
        *   `https://jinjamap-*.run.app/*`
        *   `http://localhost/*` (for local testing)

## 📝 License

This project is for educational and portfolio purposes.
