# protonmailer

A local-first email automation dashboard built with FastAPI, SQLAlchemy, APScheduler, and SMTP (Proton Mail Bridge-ready). It lets you manage accounts, contacts, templates, and campaigns, then schedule and send personalized emails.

## Requirements
- Python 3.11+
- Dependencies from `requirements.txt`
- Proton Mail Bridge (or any SMTP service) if you want to send real mail

## Setup (automated)
1. **Run the setup script** (creates the virtual environment, installs dependencies, and copies `.env.example` to `.env` if missing).
   ```bash
   bash setup.sh
   ```
   - To start fresh, add `--reset` to remove any existing `.venv` and `.env` first: `bash setup.sh --reset`.
2. **Activate the virtual environment.**
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - Windows (CMD):
     ```cmd
     .venv\Scripts\activate.bat
     ```
3. **Start the app.**
   ```bash
   uvicorn protonmailer.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   - Stop the app cleanly with `Ctrl+C` in the same terminal. If you need to force-close from another shell, run `pkill -f "uvicorn protonmailer.main:app"` to terminate the server and in-process scheduler.
4. **Adjust configuration as needed.** The setup script creates `.env` from `.env.example` when missing. Key settings:
   - `DATABASE_URL` (defaults to SQLite)
   - `APP_HOST` / `APP_PORT` (bind to `127.0.0.1` for local-only use)
   - `ADMIN_USERNAME` / `ADMIN_PASSWORD` (UI login)
   - `SESSION_SECRET` (session signing; change this)

## Usage (step-by-step)
1. Open the UI at http://127.0.0.1:8000/ui/login and sign in with your admin credentials.
2. Add an SMTP account (e.g., Proton Mail Bridge host/port/username/password) on the Accounts page.
3. Add contacts on the Contacts page (manual entry or CSV import).
4. Create an email template, then build a campaign that targets specific tags.
5. Let the in-process scheduler enqueue due campaign emails and send queued messages automatically.
6. Monitor the dashboard for queued, sent, and failed items. The UI is intended for local use only; do not expose it to the internet without additional hardening.

## Stopping the software from the terminal
- Press `Ctrl+C` in the terminal running `uvicorn` to stop the web server and scheduler.
- If the process was started elsewhere or detached, run `pkill -f "uvicorn protonmailer.main:app"` to force-stop all instances.

## Development helpers
- Run the app: `make run`
- Run tests: `make test`

## Notes
- SMTP credentials are stored as provided; add real encryption for production use.
- Scheduler jobs run inside the FastAPI process; for production-grade deployments consider external schedulers and SMTP secrets management.
