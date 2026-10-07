# Train Booking Date Reminder System

A clean, modular Python web application built with Flask, SQLAlchemy, Jinja2, and Bootstrap 5 that helps passengers determine their expected train ticket booking opening date based on their planned journey date and reminds them when that booking date is approaching.

---

## 1. Problem Statement

Passengers planning train journeys often struggle to manually remember or calculate when ticket booking will open for their journey. 

This becomes difficult when:
- A passenger has multiple upcoming journeys across different dates.
- Advance booking windows (e.g., 60 days) require complex date calculations across month and leap-year boundaries.
- Passengers repeatedly visit railway booking platforms unnecessarily before booking actually opens.
- Passengers forget the booking date and lose out on ticket availability.

## 2. Solution & Objective

The **Train Booking Date Reminder System** solves this problem by allowing passengers to save planned journeys and automatically calculating their **Expected Booking Opening Date** using dynamic Python date arithmetic.

The application displays:
- Planned Journey Date & Expected Booking Opening Date
- Countdown of days remaining until booking opens
- Dynamic Booking Status (Booking Today, Booking Tomorrow, Booking Soon, Upcoming, Booking Date Passed, Journey Completed)
- Active Reminder Status indicators

> **Note on Booking Availability**: The application distinguishes between *Expected Booking Opening Date* (calculated by our system algorithm) and *Actual Ticket Availability*. It displays clear guidance to check the railway booking platform when the calculated booking date arrives.

---

## 3. Technology Stack

- **Backend**: Python 3.11+, Flask 3.1+
- **Frontend**: HTML5, CSS3, JavaScript (ES6), Jinja2 Templates, Bootstrap 5.3
- **Database**: SQLite (Development/Production ready), Flask-SQLAlchemy 3.1+ (ORM)
- **Data Processing**: pandas, NumPy
- **Configuration**: python-dotenv, Centralized `config.py`
- **Testing**: pytest 9.1+

---

## 4. Features

- **Automated Booking Opening Date Calculation**: Dynamically computes `Journey Date - Configured Booking Window (60 Days)` taking into account leap years, month boundaries, and year boundaries.
- **Interactive Quick Booking Calculator**: Real-time AJAX preview of expected booking opening dates on the homepage and journey forms.
- **Journey Management (CRUD)**: Create, view, update, and delete planned train journeys.
- **Dashboard & Analytics**: Filter journeys by status, search by stations/trains, sort by dates, and view aggregate summary metrics.
- **Dynamic Status & Reminders**: Real-time status indicators (Booking Today, Booking Soon, Active Reminder).
- **Server-side & Client-side Validation**: Robust validation preventing past dates, empty stations, or identical source and destination stations.
- **JSON REST API**: Endpoints for programmatic access and AJAX frontend integrations.
- **Responsive UI**: Polished modern desktop and mobile user interface built with Bootstrap 5 cards, badges, modal dialogs, and alerts.

---

## 5. System Architecture

```text
                    USER / BROWSER
                          │
                          ▼
                    FLASK ROUTES
                     (main, api)
                          │
                          ▼
                INPUT VALIDATION
             (app.utils.validators)
                          │
                          ▼
                    SERVICE LAYER
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   Booking Date        Reminder          pandas / NumPy
   Calculation         Status            Data Processing
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                   SQLALCHEMY ORM
                  (app.models.journey)
                          │
                          ▼
                   SQLITE DATABASE
```

---

## 6. Project Structure

```text
train-booking-reminder/
│
├── app/
│   ├── __init__.py           # Application Factory (create_app)
│   ├── config/               # Config module initialization
│   ├── models/               # SQLAlchemy DB Models (Journey)
│   ├── routes/               # Flask Blueprints (main, api)
│   ├── services/             # Core Business Logic (booking_service, reminder_service)
│   ├── utils/                # Helpers, Data Processing, Validators
│   ├── templates/            # Jinja2 HTML Templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── dashboard.html
│   │   ├── add_journey.html
│   │   ├── edit_journey.html
│   │   ├── journey_detail.html
│   │   ├── 404.html
│   │   ├── 500.html
│   │   └── components/       # Reusable UI Components
│   │       ├── navbar.html
│   │       ├── footer.html
│   │       ├── journey_card.html
│   │       └── alerts.html
│   └── static/               # CSS and JS Assets
│       ├── css/style.css
│       └── js/main.js
│
├── tests/                    # Pytest Suite
│   ├── test_booking_service.py
│   ├── test_reminder_service.py
│   ├── test_journey_model.py
│   ├── test_routes.py
│   └── test_validators.py
│
├── instance/                 # SQLite Database Storage
├── .env                      # Local Environment Variables
├── .env.example              # Example Configuration
├── .gitignore                # Git Ignore Rules
├── config.py                 # Centralized Configuration Source
├── requirements.txt          # Dependencies
├── run.py                    # Application Entrypoint
└── README.md                 # Project Documentation
```

---

## 7. Installation & Setup

### Prerequisites
- Python 3.10+ installed

### Step 1: Clone / Navigate to Project Directory
```bash
cd d:/VIT/PROJECT/PYTHON/IMPLEMENTATION
```

### Step 2: Create Virtual Environment (Optional but recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 8. Configuration

Copy `.env.example` to `.env`:

```env
SECRET_KEY=dev-secret-key-train-reminder-2026
DATABASE_URL=sqlite:///train_reminder.db
DEBUG=True
HOST=127.0.0.1
PORT=5000
BOOKING_WINDOW_DAYS=60
REMINDER_DAYS_BEFORE=1
APPLICATION_NAME=Train Booking Date Reminder System
```

---

## 9. Running the Application

Start the Flask development server:

```bash
python run.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

The SQLite database (`instance/train_reminder.db`) and tables will be created automatically on startup.

---

## 10. API Documentation

The application exposes JSON REST API endpoints under `/api/v1`:

### 1. Calculate Expected Booking Date (AJAX helper)
- **POST** `/api/v1/calculate-booking-date`
- **Request Body**: `{"journey_date": "2026-12-20"}`
- **Response**:
```json
{
  "booking_window_days": 60,
  "days_until_booking": 14,
  "days_until_journey": 74,
  "expected_booking_date": "2026-10-21",
  "expected_booking_date_formatted": "21 October 2026",
  "journey_date": "2026-12-20",
  "reminder_active": false,
  "reminder_text": "Scheduled (Reminder in 13 days)",
  "status_code": "UPCOMING",
  "status_text": "Booking opens in 14 days",
  "success": true
}
```

### 2. Get All Journeys
- **GET** `/api/v1/journeys?q=Chennai&status=all&sort=booking_date`

### 3. Get Single Journey
- **GET** `/api/v1/journeys/<id>`

---

## 11. Testing

Run the automated pytest suite:

```bash
pytest -v
```

Tests cover:
- Booking calculation date arithmetic (normal, month boundary, year boundary, leap year)
- Reminder service logic
- SQLAlchemy Journey model methods
- Input validation rules
- Web routes & REST API endpoints

---

## 12. Future Enhancements

- **Email & SMS Integration**: Send automatic email notifications via SendGrid/SMTP or SMS via Twilio when booking date opens.
- **User Authentication**: Add login/signup with multi-user journey management.
- **Official Railway API Sync**: Verify real-time ticket availability on railway booking APIs.
