# Public Service Request System (Mini eCitizen-style)

A Flask + SQLite web app where citizens report local service issues
(broken streetlights, water issues, garbage, etc.) and admins triage them.

## Features
- Citizen registration & login (passwords hashed with Werkzeug)
- Submit requests with category, location, description, optional image
- Auto-generated reference numbers (e.g. `PSR-2025-000001`)
- Citizen dashboard with reference, submission date, status
- Admin dashboard: all requests, filters, status updates, analytics
- Status lifecycle: Pending → In Progress → Resolved
- Role-based access control (403 page for non-admins)
- Responsive UI with mobile navigation

## Requirements
- Python 3.9+
- Flask 3.x (see `requirements.txt`)

## Setup

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py