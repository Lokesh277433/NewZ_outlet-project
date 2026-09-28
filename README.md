# News Outlet

A national news website inspired by The Guardian and Times Now — built with Django, server-rendered templates, vanilla JS, and custom CSS.

## Features

- **Public site**: Homepage with lead story grid, section rails, article pages, search, author pages
- **Breaking news bar** with animated ticker
- **Authentication**: Unique-email account, email/password login, dynamic password change, and a rate-limited email OTP password reset
- **Roles**: Reader, staff writer, and superuser views
- **Newsroom**: Draft → review → publish workflow, editorial auto-approve, staff management, article status history, tags, and homepage pinning
- **Live wire feed**: Latest headlines from GNews for signed-in users
- **Comments & bookmarks** with AJAX (vanilla JS + CSRF)
- **Responsive** layout with mobile hamburger nav

## Quick start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_groups
python manage.py seed_data
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Visit http://127.0.0.1:8000/

Copy `.env.example` to `.env` and fill in your Django secret, GNews key, SMTP email credentials, and optional OpenWeatherMap key. `.env` is ignored by Git, so those values stay local.

## Docker (EC2 / Linux)

On an Amazon Linux or Ubuntu EC2 instance, install Docker, then from the project directory:

```bash
docker build -t news-outlet .
docker run -d --name news-outlet -p 8000:8000 \
  -e SECRET_KEY='replace-with-a-long-random-string' \
  -e ALLOWED_HOSTS='*' \
  -v news_data:/app/data \
  --restart unless-stopped \
  news-outlet
```

Or with Compose:

```bash
docker compose up -d --build
```

Open security group port **8000** (or map `-p 80:8000` and open port 80). Visit `http://YOUR_EC2_PUBLIC_IP:8000/`.

Demo logins after seed: `editor@newsoutlet.local` / `editor123`, `journalist@newsoutlet.local` / `journalist123`. SQLite and uploaded media persist in the `news_data` volume.

### Demo accounts (after seed_data)

| Email   | Password       | Role        |
|-----------|----------------|-------------|
| editor@newsoutlet.local    | editor123      | Superuser      |
| journalist@newsoutlet.local| journalist123  | Staff writer  |

## URL map

| Path | Description |
|------|-------------|
| `/` | Homepage |
| `/section/<slug>/` | Category listing |
| `/article/<slug>/` | Article detail |
| `/search/?q=` | Search |
| `/author/<username>/` | Author page |
| `/accounts/register/` | Register |
| `/accounts/login/` | Login |
| `/accounts/profile/` | Profile |
| `/newsroom/` | Newsroom dashboard |
| `/admin/` | Django admin |

## Stack

- Django 5.2 + SQLite (local)
- Media files on disk (`media/`)
- HTML templates + custom CSS (`static/css/main.css`) + vanilla JS (`static/js/main.js`)
