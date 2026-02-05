# Videoflix - Backend API

**Videoflix** is a Django REST API for a video streaming platform.
It provides user authentication, video management, and **HLS adaptive streaming** with multiple resolutions (480p, 720p, 1080p).

Videos are uploaded via Django Admin, automatically converted to HLS format using **FFmpeg** in background tasks (**Django RQ + Redis**), and streamed to authenticated users.

This backend is designed to be consumed by a separate frontend (not included in this repository).

---

## Features

- **Authentication (JWT + HTTP-only Cookies)**
  - Registration with email verification
  - Login (sets `access_token` + `refresh_token` cookies)
  - Token refresh (cookie-based)
  - Logout (clears cookies + blacklists refresh token)
  - Password reset via email
- **Video Streaming (HLS)**
  - Automatic conversion to HLS format (480p, 720p, 1080p)
  - Adaptive bitrate streaming
  - Background processing via Django RQ
- **Video Management**
  - Categories (Drama, Romance, Action, Documentary, Tutorial, Vlog)
  - Thumbnails
  - Sorted by creation date (newest first)
- **User isolation**
  - Only authenticated users can access videos
- **Admin Interface**
  - Upload and manage videos
  - User management
- **Docker Ready**
  - Full Docker Compose setup
  - PostgreSQL + Redis included
- **Testing**
  - Comprehensive test suite with pytest

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 6.0 |
| API | Django REST Framework |
| Auth | SimpleJWT (JWT in HTTP-only cookies) |
| Video Processing | FFmpeg (HLS conversion) |
| Background Tasks | Django RQ + Redis |
| Database | PostgreSQL 17 |
| Cache | Redis 7 |
| Web Server | Gunicorn |
| Containerization | Docker + Docker Compose |
| Testing | pytest, pytest-django, coverage |

---

## Requirements

### For Docker Setup (Recommended)
- **Docker** (20.10+)
- **Docker Compose** (v2.0+)
- **Git**

### For Local Development (Without Docker)
- **Python 3.12+**
- **pip**
- **PostgreSQL 17**
- **Redis 7**
- **FFmpeg** (installed globally)
- **Git**

---

## FFmpeg (Required)

This project converts uploaded videos to HLS format for adaptive streaming.
FFmpeg is required for this conversion. Without FFmpeg, video processing will fail.

### Verify Installation

```bash
ffmpeg -version
```

### Install FFmpeg

#### macOS (Homebrew)
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows (Chocolatey)
```bash
choco install ffmpeg
```

> **Note:** When using Docker, FFmpeg is already included in the container.

---

## Setup with Docker (Recommended)

### 1. Clone Repository

```bash
git clone <repository-url>
cd backend
```

### 2. Environment Setup

#### macOS / Linux
```bash
cp .env.template .env
```

#### Windows (Command Prompt)
```bash
copy .env.template .env
```

### 3. Configure Environment Variables

Open `.env` and configure the following variables:

```bash
# Django superuser (created automatically on first start)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=your_secure_password
DJANGO_SUPERUSER_EMAIL=admin@example.com

# Django core
SECRET_KEY="your-secret-key-here"
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS / CSRF (Frontend URLs)
CSRF_TRUSTED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200

# Database (Docker default values work out of the box)
DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=your_database_password
DB_HOST=db
DB_PORT=5432

# Redis (Docker default values work out of the box)
REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0

# Email (SMTP)
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@videoflix.com

# Frontend URLs (for email links)
# IMPORTANT: Adjust FRONTEND_BASE_URL to match your frontend's URL and port!
# Email links (activation, password reset) will use this URL.
FRONTEND_BASE_URL=http://localhost:4200
FRONTEND_ACTIVATE_PATH=pages/auth/activate.html
FRONTEND_RESET_PATH=pages/auth/confirm_password.html

# Cookie Security (False for local development)
SECURE_COOKIES=False
JWT_COOKIE_SAMESITE=Lax
```

### 4. Generate Your Own SECRET_KEY

Django requires a secret key for cryptographic signing.

**Option 1 (recommended):**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated key into your `.env` file:
```bash
SECRET_KEY='your-generated-secret-key-here'
```

**Option 2:**
Use an online generator: https://djecrety.ir/

### 5. Email Configuration

For email functionality (registration confirmation, password reset), configure SMTP settings.

**For Testing (Ethereal):**
1. Go to https://ethereal.email/create
2. Create a test account
3. Use the provided SMTP credentials in your `.env`

**For Production:**
Use your actual SMTP provider (e.g., SendGrid, Mailgun, Gmail SMTP).

> **⚠️ Important: Frontend URL Configuration**
>
> The `FRONTEND_BASE_URL` in your `.env` file determines where email links (account activation, password reset) will point to.
>
> - If your frontend runs on a different port (e.g., `http://localhost:5000`), you **must** update `FRONTEND_BASE_URL` accordingly
> - For production, set this to your actual frontend domain (e.g., `https://yourdomain.com`)
> - The paths `FRONTEND_ACTIVATE_PATH` and `FRONTEND_RESET_PATH` can also be customized if your frontend uses different routes

### 6. Start Docker Containers

```bash
docker compose up --build
```

This will:
- Start PostgreSQL database
- Start Redis cache/queue
- Run Django migrations
- Create superuser (from environment variables)
- Start RQ worker for background tasks
- Start Gunicorn web server

### 7. Access the Application

| Service | URL |
|---------|-----|
| API | http://localhost:8000/api/ |
| Admin Panel | http://localhost:8000/admin/ |
| RQ Dashboard | http://localhost:8000/django-rq/ |

---

## Setup for Local Development (Without Docker)

### 1. Clone Repository

```bash
git clone <repository-url>
cd backend
```

### 2. Create and Activate Virtual Environment

```bash
python3 -m venv env
```

#### macOS / Linux
```bash
source env/bin/activate
```

#### Windows
```bash
env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Setup

```bash
cp .env.template .env
```

Configure `.env` as described above, but change:
```bash
DB_HOST=localhost
REDIS_HOST=localhost
REDIS_LOCATION=redis://localhost:6379/1
```

### 5. Start PostgreSQL and Redis

Make sure PostgreSQL and Redis are running locally.

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Start RQ Worker (Background Tasks)

In a separate terminal:
```bash
python manage.py rqworker default
```

### 9. Start Development Server

```bash
python manage.py runserver
```

Open: http://127.0.0.1:8000/

---

## API Endpoints

Base URL: `/api/`

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register/` | Register new user |
| GET | `/api/activate/<uidb64>/<token>/` | Activate account |
| POST | `/api/login/` | Login (sets cookies) |
| POST | `/api/logout/` | Logout (clears cookies) |
| POST | `/api/token/refresh/` | Refresh access token |
| POST | `/api/password_reset/` | Request password reset |
| POST | `/api/password_confirm/<uidb64>/<token>/` | Confirm new password |

### Video Streaming

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/video/` | List all videos |
| GET | `/api/video/<id>/<resolution>/index.m3u8` | HLS playlist |
| GET | `/api/video/<id>/<resolution>/<segment>/` | HLS segment |

**Available Resolutions:** `480p`, `720p`, `1080p`

---

## Authentication Flow

### Registration
```bash
POST /api/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "confirmed_password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "user": { "id": 1, "email": "user@example.com" },
  "token": "activation_token"
}
```
User receives activation email with link to frontend.

### Login
```bash
POST /api/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "detail": "Login successful",
  "user": { "id": 1, "username": "user@example.com" }
}
```

**Cookies Set:**
- `access_token` (HttpOnly, short-lived)
- `refresh_token` (HttpOnly, long-lived)

### Token Refresh
```bash
POST /api/token/refresh/
```
Uses `refresh_token` cookie, returns new `access_token`.

### Logout
```bash
POST /api/logout/
```
Blacklists refresh token, deletes cookies.

---

## Video Upload and Streaming

### Upload Video (Admin Panel)

1. Go to http://localhost:8000/admin/
2. Login with superuser credentials
3. Navigate to **Videos** > **Add Video**
4. Fill in title, description, category
5. Upload video file (supported: `.mp4`, `.mov`, `.avi`, `.mkv`, `.flv`, `.wmv`)
6. Optionally upload thumbnail image
7. Save

Video is automatically converted to HLS (480p, 720p, 1080p) in background.

### Stream Video (API)

1. Get video list:
```bash
GET /api/video/
Authorization: (via cookie)
```

2. Get HLS playlist:
```bash
GET /api/video/1/720p/index.m3u8
```

3. Video player fetches segments automatically from:
```bash
GET /api/video/1/720p/segment_000.ts
GET /api/video/1/720p/segment_001.ts
...
```

---

## Production Setup

### Update `.env` for Production

```bash
DEBUG=False
SECRET_KEY=<strong-production-secret>
SECURE_COOKIES=True
JWT_COOKIE_SAMESITE=None
ALLOWED_HOSTS=api.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
FRONTEND_BASE_URL=https://yourdomain.com
```

### SSL/HTTPS

- Use a reverse proxy (Nginx, Traefik) with SSL certificates
- Enable `USE_X_FORWARDED_PROTO=True` if behind a proxy

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

---

## Project Structure

```
backend/
|
+-- apps/                               # Django applications
|   |
|   +-- content_app/                    # Video content management
|   |   +-- api/                        # REST API layer
|   |   |   +-- serializers.py          # DRF serializers
|   |   |   +-- views.py                # API views (video list, HLS streaming)
|   |   |   +-- urls.py                 # API routes
|   |   |   +-- permissions.py          # Custom permissions
|   |   +-- tests/                      # Test suite
|   |   +-- models.py                   # Video model
|   |   +-- signals.py                  # Post-save/delete hooks (HLS conversion)
|   |   +-- tasks.py                    # Background tasks (FFmpeg conversion)
|   |   +-- utils.py                    # HLS path helpers
|   |   +-- admin.py                    # Admin configuration
|   |
|   +-- user_auth_app/                  # User authentication
|       +-- api/                        # REST API layer
|       |   +-- serializers.py          # Auth serializers
|       |   +-- views.py                # Auth views (register, login, etc.)
|       |   +-- urls.py                 # Auth routes
|       |   +-- permissions.py          # Custom permissions
|       +-- tests/                      # Test suite
|       +-- templates/                  # Email templates
|       +-- authentication.py           # Custom JWT cookie authentication
|       +-- tasks.py                    # Email sending tasks
|       +-- utils.py                    # Auth helpers (cookies, tokens)
|       +-- admin.py                    # User admin configuration
|
+-- core/                               # Django project configuration
|   +-- settings.py                     # Global settings
|   +-- urls.py                         # Root URL configuration
|   +-- wsgi.py                         # WSGI entry point
|   +-- asgi.py                         # ASGI entry point
|
+-- media/                              # User-uploaded files (videos, thumbnails)
+-- static/                             # Collected static files
+-- assets/                             # Static assets (logo, etc.)
|
+-- docker-compose.yml                  # Docker Compose configuration
+-- backend.Dockerfile                  # Docker image definition
+-- backend.entrypoint.sh               # Container startup script
|
+-- .env.template                       # Environment variables template
+-- requirements.txt                    # Python dependencies
+-- manage.py                           # Django management script
```

---

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
coverage run -m pytest
coverage report -m --include="apps/*" --omit="*/migrations/*,*/tests/*"
```

### HTML Coverage Report

```bash
coverage html
open htmlcov/index.html
```

---

## Docker Commands

### Start Containers
```bash
docker compose up -d
```

### Stop Containers
```bash
docker compose down
```

### View Logs
```bash
docker compose logs -f web
```

### Rebuild After Changes
```bash
docker compose up --build
```

### Access Container Shell
```bash
docker exec -it videoflix_backend bash
```

### Run Django Commands in Container
```bash
docker exec -it videoflix_backend python manage.py <command>
```

---

## Troubleshooting

### Videos Not Converting

1. Check RQ worker is running:
   ```bash
   docker compose logs -f web | grep rqworker
   ```

2. Check RQ dashboard: http://localhost:8000/django-rq/

3. Verify FFmpeg is available:
   ```bash
   docker exec -it videoflix_backend ffmpeg -version
   ```

### Email Not Sending

1. Verify SMTP settings in `.env`
2. Check for errors in logs:
   ```bash
   docker compose logs -f web
   ```
3. Test with Ethereal email for debugging

### Database Connection Issues

1. Ensure PostgreSQL container is healthy:
   ```bash
   docker compose ps
   ```

2. Check database logs:
   ```bash
   docker compose logs db
   ```

---

## License

MIT License