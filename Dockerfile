# ==========================================
# Stage 1: Build the React Frontend
# ==========================================
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Build production assets into /app/frontend/dist
COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Python Backend & Static Serving
# ==========================================
FROM python:3.11-slim
WORKDIR /app

# Install basic OS utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application code
COPY backend/ ./backend/

# Copy compiled frontend from Stage 1 into /app/frontend/dist
# (FastAPI mounts this directory automatically)
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

WORKDIR /app/backend

# Render dynamically sets $PORT (defaults to 8000 for local Docker runs)
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
