# protonmailer

A local-first email automation dashboard built with FastAPI, SQLAlchemy, APScheduler, and SMTP (Proton Mail Bridge-ready). It lets you manage accounts, contacts, templates, and campaigns, then schedule and send personalized emails.

## Requirements
- Python 3.11+
- Dependencies from `requirements.txt`
- Proton Mail Bridge (or any SMTP service) if you want to send real mail

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the example environment file and adjust values:
   ```bash
   cp .env.example .env
   ```
   Key settings:
   - `DATABASE_URL` (defaults to SQLite)
   - `APP_HOST` / `APP_PORT` (bind to `127.0.0.1` for local-only use)
   - `ADMIN_USERNAME` / `ADMIN_PASSWORD` (UI login)
   - `SESSION_SECRET` (session signing; change this)
4. Run the app:
   ```bash
   uvicorn protonmailer.main:app --host 127.0.0.1 --port 8000 --reload
   ```

## Usage
1. Visit http://127.0.0.1:8000/ui/login and sign in with your admin credentials.
2. Add an SMTP account (e.g., Proton Mail Bridge host/port/username/password).
3. Add contacts (manually or via CSV import on the Contacts page).
4. Create an email template and a campaign targeting specific tags.
5. The in-process scheduler enqueues due campaign emails and sends queued messages automatically.
6. Monitor the dashboard for queue, sent, and failed items. The UI is intended for local use only; do not expose it to the internet without additional hardening.

## Development helpers
- Run the app: `make run`
- Run tests: `make test`

## Notes
- SMTP credentials are stored as provided; add real encryption for production use.
- Scheduler jobs run inside the FastAPI process; for production-grade deployments consider external schedulers and SMTP secrets management.
