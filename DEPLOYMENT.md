# Deployment Guide: Render.com

This project is configured as a unified full-stack application using a multi-stage **Docker** build. 
When deployed, it builds the React frontend, sets up Python 3.11 with all cryptographic/scientific libraries, and serves both the API and the React UI from a single service with zero CORS configuration needed.

---

## 1. Commit and Push to GitHub

Ensure all files (including `Dockerfile`, `.dockerignore`, and `render.yaml`) are pushed to your GitHub repository:

```bash
git add .
git commit -m "Configure Docker and Render deployment files"
git push origin main
```

---

## 2. Deploy on Render (2 Methods)

### Method A: Connect as a Web Service (Recommended)

1. Go to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** (top right) $\rightarrow$ **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your repository.
4. Render will auto-fill most settings. Ensure the following:
   * **Name:** `qsfw-watermarking` (or your choice)
   * **Region:** Any region close to you (e.g. Singapore, Frankfurt, Oregon)
   * **Branch:** `main`
   * **Language / Runtime:** **Docker** (Render will detect the `Dockerfile` in the root)
   * **Instance Type:** **Free** ($0/month)
5. Under **Advanced** $\rightarrow$ **Add Environment Variable** (optional, recommended for production secrets):
   * `OFFLINE_MODE` = `true`
   * `QSFW_WATERMARK_SECRET` = (Enter any long random string or leave blank for demo secret)
   * `QSFW_KEYSTORE_PASSWORD` = (Enter any secure password or leave blank for demo password)
6. Click **Deploy Web Service**.

---

### Method B: Deploy using Render Blueprint

Because this repository contains a `render.yaml` file:
1. In the Render Dashboard, click **New +** $\rightarrow$ **Blueprint**.
2. Select your repository.
3. Render reads `render.yaml` and sets up the Docker Web Service and secrets automatically.
4. Click **Apply**.

---

## 3. What to Expect After Deployment

* **Build Phase (~3-5 minutes on first build):** Render will run the multi-stage build:
  1. Installs Node.js dependencies and compiles the React application to static assets.
  2. Installs Python dependencies (`fastapi`, `uvicorn`, `cryptography`, `PyMuPDF`, `opencv-python-headless`, etc.).
  3. Launches Uvicorn dynamically bound to Render's allocated `$PORT`.
* **Accessing Your Live App:**
  * UI: `https://<your-service-name>.onrender.com/`
  * Interactive API Docs (Swagger): `https://<your-service-name>.onrender.com/docs`
  * API Health/Endpoints: `https://<your-service-name>.onrender.com/api/dashboard`

---

## 4. Free Tier Notes
* **Cold Starts:** Free services on Render enter sleep mode after 15 minutes of inactivity. When accessed after sleeping, the initial request takes ~30–50 seconds to boot up.
* **Storage Persistence:** Free tier instances have ephemeral file systems. Any SQLite data or uploaded files in `backend/data` will be reset on a new deployment or cold restart.
