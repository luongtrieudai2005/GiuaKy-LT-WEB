# TaskFlow — Task Manager Web Application

A production-ready task management web application built to demonstrate **web application deployment** techniques including Docker, Nginx reverse proxy, HTTPS/SSL, and CI/CD with GitHub Actions.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Database | MongoDB 7.0 (via Beanie ODM + Motor) |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Reverse Proxy | Nginx 1.25 |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Authentication | JWT (JSON Web Token) via python-jose |

---

## Project Structure

```
task-manager/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD pipeline
├── backend/
│   ├── routers/
│   │   ├── users.py            # Auth endpoints (register, login)
│   │   ├── tasks.py            # Task CRUD endpoints
│   │   └── categories.py       # Category CRUD endpoints
│   ├── main.py                 # FastAPI app entry point
│   ├── models.py               # MongoDB document models (Beanie)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── database.py             # JWT helpers, password hashing
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Backend container image
├── frontend/
│   ├── index.html              # Single-page application
│   ├── style.css               # Dark minimal UI styles
│   └── app.js                  # Fetch API calls to backend
├── nginx/
│   ├── nginx.conf              # Reverse proxy + SSL config
│   └── ssl/                    # SSL certificates (not committed)
│       ├── cert.pem
│       └── key.pem
├── docker-compose.yml          # Orchestrates all services
├── generate-ssl.bat            # Generate self-signed cert (Windows)
├── generate-ssl.sh             # Generate self-signed cert (Linux/Mac)
├── .env.example                # Environment variables template
└── README.md
```

---

## Prerequisites

Make sure the following are installed on your machine:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- [OpenSSL](https://slproweb.com/products/Win32OpenSSL.html) — for generating SSL certificates
  - Windows users with Git Bash already have OpenSSL available

---

## Setup & Running (Local with Docker)

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-username/taskmanager.git
cd taskmanager
```

### Step 2 — Create environment file

```bash
cp .env.example .env
```

Open `.env` and fill in your values. Key variables:

```env
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your_strong_password

# Must match the credentials above
MONGODB_URL=mongodb://admin:your_strong_password@mongo:27017/?authSource=admin

MONGODB_DB_NAME=taskmanager
SECRET_KEY=your_random_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=https://localhost
DOMAIN=localhost
```

To generate a strong `SECRET_KEY`:
```bash
openssl rand -hex 32
```

### Step 3 — Generate SSL certificate (run once)

**Windows:**
```bat
generate-ssl.bat
```

**Linux / Mac / Git Bash:**
```bash
bash generate-ssl.sh
```

This creates `nginx/ssl/cert.pem` and `nginx/ssl/key.pem`.

### Step 4 — Build and start all services

```bash
docker compose up --build
```

Expected output when all services are ready:
```
mongo    | MongoDB starting...
fastapi  | Connected to MongoDB: taskmanager
fastapi  | INFO: Uvicorn running on http://0.0.0.0:8000
nginx    | ready for start up
```

### Step 5 — Open the application

| URL | Description |
|---|---|
| `https://localhost` | Main application (TaskFlow UI) |
| `https://localhost/api/docs` | FastAPI Swagger UI (API documentation) |
| `https://localhost/api/health` | Health check endpoint |

> **Note:** Your browser will show a security warning for the self-signed certificate.
> Click **Advanced → Proceed to localhost** to continue.
> This is expected behavior for local development certificates.

---

## Running Locally (without Docker)

Useful for development and debugging.

### Step 1 — Start a MongoDB instance

```bash
docker run -d -p 27017:27017 --name mongo-local mongo:7.0
```

### Step 2 — Create and activate virtual environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment

Create `backend/.env`:
```env
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DB_NAME=taskmanager
SECRET_KEY=dev_secret_key_local
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=http://localhost:8000
```

### Step 5 — Run the server

```bash
python -m uvicorn main:app --reload
```

Open `http://localhost:8000` in your browser.

> **Note:** When running locally, `API_BASE` in `frontend/app.js` must be set to `''` (empty string).
> When running via Docker + Nginx, it must be `'/api'`.

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create a new account |
| POST | `/auth/login` | Login, returns JWT token |
| GET | `/auth/me` | Get current user profile |

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| GET | `/tasks/` | List all tasks (supports `?status=`, `?priority=`, `?category_id=`) |
| POST | `/tasks/` | Create a new task |
| GET | `/tasks/{id}` | Get a single task |
| PATCH | `/tasks/{id}` | Partially update a task |
| DELETE | `/tasks/{id}` | Delete a task |

### Categories

| Method | Endpoint | Description |
|---|---|---|
| GET | `/categories/` | List all categories |
| POST | `/categories/` | Create a new category |
| PATCH | `/categories/{id}` | Update a category |
| DELETE | `/categories/{id}` | Delete a category (tasks are unlinked, not deleted) |

All endpoints except `/auth/register` and `/auth/login` require:
```
Authorization: Bearer <your_jwt_token>
```

---

## CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/deploy.yml`) runs automatically on every push to `main`:

```
Push to main
    │
    ▼
Job 1: Test ──── fail ──→ Pipeline stops
    │ pass
    ▼
Job 2: Build Docker image ──── fail ──→ Pipeline stops
    │ pass
    ▼
Job 3: Deploy to VPS (requires secrets)
```

To enable the deploy job, add these secrets to your GitHub repository
(**Settings → Secrets and variables → Actions**):

| Secret | Value |
|---|---|
| `VPS_HOST` | IP address or domain of your server |
| `VPS_USER` | SSH username (e.g. `ubuntu`) |
| `VPS_SSH_KEY` | Contents of your private SSH key (`~/.ssh/id_rsa`) |

---

## Stopping the Application

```bash
# Stop all containers (preserves data)
docker compose down

# Stop and remove all data (full reset)
docker compose down -v
```

---

## Deployment Architecture

```
Internet
    │
    ▼ port 443 (HTTPS)
┌─────────────────────────────────────────┐
│  Nginx (reverse proxy)                  │
│  - SSL termination (Let's Encrypt)      │
│  - Serves frontend static files         │
│  - Proxies /api/* → FastAPI:8000        │
└──────────────┬──────────────────────────┘
               │ Docker internal network
       ┌───────┴────────┐
       ▼                ▼
  ┌─────────┐     ┌──────────┐
  │ FastAPI │────▶│ MongoDB  │
  │ :8000   │     │ :27017   │
  └─────────┘     └──────────┘
```

---

**Course:** Web Programming and Applications (503073)
**Institution:** Ton Duc Thang University — Faculty of Information Technology
**Semester:** 2 — Academic Year 2025–2026