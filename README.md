# Murang'a County Public Service Request System

A web-based platform built for Murang'a County where citizens can report local infrastructure and service issues (like broken streetlights, water leaks, or illegal dumping). Admins have a dedicated portal to review these reports, set timelines, and update their statuses.

## Evaluation Credentials

To make testing easy, an Admin account is automatically created when the app runs for the first time. 

Admin Login:
- Email: admin.muranga@gmail.com
- Password: Admin@12345

To test the Citizen view, simply click Register on the homepage and create a new account.

## What it does

- Citizen accounts: Users can register, log in, update their profile picture, or delete their account entirely.
- Issue reporting: Citizens can submit a request with a specific category, title, ward location, description, and an optional photo.
- Auto-referencing: Every submitted request gets a unique reference number (e.g., MCG-001) for easy tracking.
- Tracking: Citizens get a personal dashboard showing their past requests along with a progress bar and status badges.
- Admin portal: A separate login for admins to view all incoming requests, update statuses (Pending, In Progress, Resolved), add internal notes, and set an estimated resolution timeline.
- Analytics: The admin dashboard includes quick stat cards showing total requests, pending cases, and resolved ones.
- Access control: Citizens are strictly blocked (HTTP 403) from accessing the admin dashboard.

## Built With

- Python (Flask)
- SQLite
- HTML / CSS (Vanilla, no heavy frameworks)
- Jinja2 templating

## Running it locally

1. Make sure Python 3.9 or newer is installed.
2. Clone this repo and move into the folder:
   git clone <your-repo-url>
   cd public-service-request-system
3. Create and activate a virtual environment:
   py -m venv .venv
   .venv\Scripts\activate
4. Install the required packages:
   pip install -r requirements.txt
5. Start the development server:
   python app.py
6. Open http://127.0.0.1:5000 in your browser.

## Project Structure

public-service-request-system/
│
├── app.py                  Main Flask app (routes, database, logic)
├── requirements.txt        Python dependencies
├── README.md               
│
├── instance/               
│   └── muranga.db          SQLite database (auto-generated)
│
├── static/
│   ├── css/
│   │   └── style.css       Main stylesheet
│   └── uploads/            Uploaded request & profile images
│
└── templates/
    ├── admin.html          Admin dashboard
    ├── admin_login.html    Separate admin login page
    ├── auth.html           Login/Register for citizens
    ├── base.html           Shared layout and nav
    ├── dashboard.html      Citizen request dashboard
    ├── index.html          Landing page
    ├── new-request.html    Request submission form
    ├── profile.html        Citizen profile settings
    └── users.html          Admin view of all citizens