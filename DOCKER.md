# Docker Deployment Guide for DocIntel

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available for Docker

## Quick Start (Production)

### 1. Clone and Configure

```bash
cd IDUS_Project

# Create backend .env file with your Groq API key
echo "GROQ_API_KEY=your_groq_api_key_here" > backend/.env
```

### 2. Build and Run

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f
```

### 3. Access the Application

- **Frontend:** http://localhost (port 80)
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Development Mode

For development with hot-reload:

```bash
# Start development containers
docker-compose -f docker-compose.dev.yml up --build

# Frontend available at: http://localhost:5173
# Backend available at: http://localhost:8000
```

## Container Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                  (docintel-network)                      │
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │    Frontend      │      │    Backend       │        │
│  │    (nginx)       │─────▶│   (FastAPI)      │        │
│  │    Port: 80      │      │   Port: 8000     │        │
│  └──────────────────┘      └──────────────────┘        │
│                                    │                     │
│                                    ▼                     │
│                            ┌──────────────┐             │
│                            │   Volumes    │             │
│                            │  - data/     │             │
│                            │  - uploads/  │             │
│                            └──────────────┘             │
└─────────────────────────────────────────────────────────┘
```

## Services

### Backend Service

| Property | Value |
|----------|-------|
| Image | python:3.11-slim |
| Port | 8000 |
| Volumes | `./backend/data:/app/data` |
| Health Check | `curl http://localhost:8000/api/health` |

**Installed Dependencies:**
- Tesseract OCR (for document text extraction)
- Poppler (for PDF processing)
- spaCy with en_core_web_sm model
- All Python requirements

### Frontend Service

| Property | Value |
|----------|-------|
| Image | nginx:alpine (production) |
| Port | 80 |
| Dependencies | Backend must be healthy |

**Features:**
- Multi-stage build (Node.js → nginx)
- Gzip compression enabled
- Static asset caching
- SPA routing support
- API proxy to backend

## Environment Variables

### Backend

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for AI features | Yes |
| `DEBUG` | Enable debug mode | No (default: False) |

### Frontend

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_URL` | Backend API URL | No (proxied via nginx) |

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Enter backend container
docker exec -it docintel-backend /bin/bash

# Check container status
docker-compose ps

# Remove all containers and volumes
docker-compose down -v

# Prune unused Docker resources
docker system prune -a
```

## Volumes and Data Persistence

Data is persisted in these directories:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./backend/data` | `/app/data` | Document store (JSON) |
| `./backend/temp_uploads` | `/app/temp_uploads` | Temporary upload files |

**Important:** Back up `./backend/data/document_store.json` to preserve your documents.

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Missing GROQ_API_KEY in .env
# - Port 8000 already in use
```

### Frontend can't reach backend

```bash
# Ensure backend is healthy
docker-compose ps

# Check nginx config
docker exec -it docintel-frontend cat /etc/nginx/conf.d/default.conf
```

### OCR not working

```bash
# Verify Tesseract is installed
docker exec -it docintel-backend tesseract --version

# Check if PDF processing works
docker exec -it docintel-backend which pdftoppm
```

### Reset everything

```bash
# Stop and remove all containers, networks, volumes
docker-compose down -v --remove-orphans

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

## Production Deployment Tips

1. **Use environment file:**
   ```bash
   docker-compose --env-file .env.production up -d
   ```

2. **Enable HTTPS:** Use a reverse proxy (Traefik, nginx) with Let's Encrypt

3. **Set resource limits:**
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
   ```

4. **Use Docker secrets** for sensitive data in production

5. **Regular backups:**
   ```bash
   # Backup document store
   docker cp docintel-backend:/app/data/document_store.json ./backup/
   ```

## Health Checks

Both services include health checks:

- **Backend:** `GET /api/health` - Returns 200 if healthy
- **Frontend:** Checks if nginx is serving on port 80

```bash
# Manual health check
curl http://localhost:8000/api/health
curl http://localhost/
```

## Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up --build -d

# Verify
docker-compose ps
```
