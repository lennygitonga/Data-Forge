# Data-Forge

**Automated Web Intelligence — Scrape any website, get insights in your inbox.**

Data-Forge is an AI-powered web scraping platform built entirely in Python. You name a website, set a schedule, and Data-Forge handles everything else — fetching the page, extracting the content, summarising it with AI, and delivering a clean report to your email automatically.

---

## What It Does

- Type any website name or URL into the dashboard
- Data-Forge resolves the URL, scrapes the page, and passes the content through Groq AI
- A structured report arrives in your inbox — summary, key points, and raw data as a CSV attachment
- Optionally set a recurring schedule and receive automatic reports every hour, day, or week

---

## Features

**AI-Powered Scraping**
The AI bot resolves plain English site names to real URLs. Type "BBC News" or "Jumia Kenya" and it figures out the correct URL automatically using the Groq LLM.

**Smart Fetching**
Pages are fetched using httpx for speed. If a site requires JavaScript to render, the app automatically falls back to Playwright with stealth mode to bypass bot detection.

**Structured Email Reports**
Every report includes an AI-written summary, a list of key points, and all extracted data formatted as a clean HTML email. Raw data is attached as a CSV file.

**Recurring Scheduler**
Jobs can be scheduled to run automatically using APScheduler. Set it once and receive reports on whatever interval you choose — hourly, every 6 hours, daily, or weekly.

**Full Web Dashboard**
A clean web interface built with Flask and Jinja2 lets you submit jobs, track their status, view history, cancel schedules, and manage your account.

**CLI Interface**
Power users can run scrapes directly from the terminal using the Typer-based CLI without opening a browser.

**Authentication**
Full user authentication with register, login, and logout. Google OAuth login is supported via Flask-Dance.

**Error Handling**
All scrape failures are caught, logged to the database, and reported to the user via a dedicated error email. Retry logic is built into both the scraper and the AI layer.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Flask |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| AI / LLM | Groq (llama-3.3-70b-versatile) |
| Static scraping | httpx + BeautifulSoup4 |
| JS site rendering | Playwright + playwright-stealth |
| Email delivery | Resend |
| Job scheduling | APScheduler |
| Authentication | Flask-Login + Flask-Bcrypt + Flask-Dance |
| CLI | Typer + Rich |

---

## Project Structure

```
Data-Forge/
├── app/
│   ├── __init__.py         Flask app factory, extensions
│   ├── config.py           Environment variable configuration
│   ├── models.py           User and Job database models
│   ├── routes.py           Web routes and API endpoints
│   ├── auth.py             Login, register, logout
│   ├── google_auth.py      Google OAuth via Flask-Dance
│   ├── scraper.py          Web fetching engine with Playwright fallback
│   ├── ai.py               Groq AI site resolver and summariser
│   ├── emailer.py          HTML email builder and Resend sender
│   ├── scheduler.py        APScheduler background job runner
│   ├── cli.py              Typer CLI commands
│   ├── templates/
│   │   ├── base.html       Master layout, navbar, footer
│   │   ├── about.html      Company story and team
│   │   ├── contact.html    Contact form and map
│   │   ├── settings.html   Account settings
│   │   ├── auth/
│   │   │   └── auth.html   Tabbed login and register
│   │   └── dashboard/
│   │       ├── home.html   Scrape form and stats
│   │       └── jobs.html   Jobs table with tabs
│   └── static/
│       └── css/
│           └── main.css    Full design system
├── run.py                  Application entry point
├── requirements.txt        Python dependencies
├── .env.example            Environment variable template
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Python 3.13 or higher
- PostgreSQL installed and running
- A Groq API key (free at console.groq.com)
- A Resend API key (free at resend.com)
- A Google OAuth client ID and secret (for Google login)

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/Data-Forge.git
cd Data-Forge
```

**2. Create and activate a virtual environment**

```bash
py -3.13 -m venv venv

# Windows
source venv/Scripts/activate

# Mac / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
playwright install
```

**4. Create the PostgreSQL database**

```bash
psql -U postgres
CREATE DATABASE data_forge;
\q
```

**5. Set up environment variables**

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

```
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/data_forge
GROQ_API_KEY=your_groq_key_here
RESEND_API_KEY=your_resend_key_here
SECRET_KEY=your_random_secret_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

**6. Run the application**

```bash
python run.py
```

Visit `http://127.0.0.1:5000` in your browser.

---

## Using the CLI

Make sure the server is running in one terminal, then use the CLI in another.

**Check server status**
```bash
python app/cli.py status
```

**Scrape a website**
```bash
python app/cli.py scrape "bbc news" --email you@example.com
```

**Scrape with a query**
```bash
python app/cli.py scrape "techcrunch" --email you@example.com --query "AI funding news"
```

**Scrape on a schedule**
```bash
python app/cli.py scrape "reuters" --email you@example.com --schedule "every 24h"
```

**List all jobs**
```bash
python app/cli.py jobs
```

**Delete a job**
```bash
python app/cli.py delete 5
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /scrape | Submit a scrape job via web form |
| POST | /api/scrape | Submit a scrape job via JSON (CLI) |
| GET | /api/jobs | List all jobs |
| DELETE | /api/jobs/{id} | Delete a job |
| GET | /health | Server health check |

---

## Limitations

Some websites actively block scrapers regardless of stealth techniques. These include sites that require user login to display content (Instagram, Facebook, LinkedIn, Twitter/X) and sites with advanced bot detection systems (Amazon, Cloudflare-protected sites). Data-Forge works best on news sites, blogs, job boards, e-commerce listings, and public data sources.

---

## Environment Variables Reference

| Variable | Description |
|---|---|
| FLASK_ENV | Set to `development` locally, `production` on server |
| DATABASE_URL | Full PostgreSQL connection string |
| GROQ_API_KEY | API key from console.groq.com |
| RESEND_API_KEY | API key from resend.com |
| SECRET_KEY | Random string for Flask session security |
| GOOGLE_CLIENT_ID | From Google Cloud Console OAuth credentials |
| GOOGLE_CLIENT_SECRET | From Google Cloud Console OAuth credentials |

---
## Author

Lenny Gitonga

## License

MIT License. See LICENSE for details.