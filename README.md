# CUFitness

A Django web application for managing a university fitness centre. Members can browse services, request a coach, and manage their profile. Coaches manage their availability and appointments. Staff manage members, coach requests, and publish articles.

---

## Tech Stack

- **Backend:** Django 6.0.1, Django REST Framework
- **Database:** SQLite (via Django ORM)
- **Frontend:** HTML/CSS templates (Django template engine)
- **Auth:** Custom user model (`CustomUser`) with email-based login

---

## Prerequisites

- Python 3.10+
- pip

---

## Setup

**1. Clone the repository**
```bash
git clone <repo-url>
cd COEN6311-SANJ
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Apply migrations**
```bash
python manage.py migrate
```

**5. Seed the database with test data**
```bash
python seed_data.py
```

**6. Run the development server**
```bash
python manage.py runserver
```

Then open http://127.0.0.1:8000 in your browser.

---

## Test Accounts

All accounts are created by `seed_data.py`.

| Role   | Email                     | Password     |
|--------|---------------------------|--------------|
| Admin  | admin@cufitness.com       | Admin@1234   |
| Staff  | staff1@cufitness.com      | Staff@1234   |
| Staff  | staff2@cufitness.com      | Staff@1234   |
| Member | member1@cufitness.com     | Member@1234  |
| Member | member2@cufitness.com     | Member@1234  |
| Member | member3@cufitness.com     | Member@1234  |
| Coach  | coach1@cufitness.com      | Coach@1234   |

> Members and coaches log in at `/login/`. Staff log in at `/staff_login/`.

---

## User Roles

**Member** — can browse public pages, manage their profile and privacy settings, request to become a coach, and book coach appointments.

**Coach** — everything a member can do, plus manage availability slots and respond to appointment requests from members.

**Staff** — separate login portal, can view/manage all members and coaches, handle coach role requests (approve/reject), publish and manage articles, and view reports.

**Admin** — superuser access via the Django admin panel at `/admin/`.

---

## Key URLs

### Public
| URL | Description |
|-----|-------------|
| `/` | Home page |
| `/services/` | Services overview |
| `/memberships/` | Membership tiers |
| `/trainers/` | Trainers page |
| `/nutrition/` | Articles (free + premium) |
| `/amenities/` | Amenities |
| `/schedule/` | Class schedule |
| `/faq/` | FAQ |
| `/policy/` | Privacy policy |
| `/about/` | About page |
| `/contact/` | Contact page |

### Authentication
| URL | Description |
|-----|-------------|
| `/register/` | New member registration |
| `/login/` | Member / coach login |
| `/logout/` | Logout |
| `/staff_login/` | Staff login |

### Member / Coach
| URL | Description |
|-----|-------------|
| `/user_profile/` | Profile page |
| `/user_settings/` | Email, password, privacy, coach request |
| `/user_inbox/` | Inbox |
| `/user_calendar/` | Calendar — appointments & availability |

### Staff
| URL | Description |
|-----|-------------|
| `/staff_home/` | Staff dashboard |
| `/staff_profile/` | Staff profile |
| `/staff_settings/` | Staff password settings |
| `/members/` | Member list |
| `/coach_requests/` | Coach role requests (approve/reject) |
| `/reports/` | Reports |
| `/articles/` | Article management |
| `/create_article/` | Create a new article |

### Coach
| URL | Description |
|-----|-------------|
| `/coach/dashboard/` | Coach overview |
| `/coach/availability/` | Manage availability slots |
| `/coach/appointments/` | Respond to appointment requests |

---

## Database Models

**CustomUser** — extends `AbstractBaseUser`. Fields: `email`, `first_name`, `last_name`, `role` (MEMBER / COACH / STAFF / ADMIN), `membership` (BASIC / STANDARD / PLATINUM / PER_SESSION), `coach_request_status` (NONE / PENDING / APPROVED / REJECTED), `workout_visibility` (PUBLIC / COACH_ONLY).

**Article** — fitness/nutrition articles published by staff. Has a `locked` flag for premium content visible only to authenticated users.

**EquipmentList** — gym equipment items with an `is_active` flag for out-of-service status.

**EquipmentBooking** — links a coach to equipment for a time slot. Prevents overlapping bookings via model-level validation.

**CoachAvailability** — time slots a coach marks as open. Prevents overlapping slots via model-level validation.

**CoachAppointment** — a member booking a coach's availability slot. Statuses: PENDING / ACCEPTED / REFUSED / CANCELLED. Prevents double-booking accepted appointments via model-level validation.

---

## Running Tests

```bash
python manage.py test CUFitness
```

The test suite covers model validation, authentication, access control, article CRUD, settings (email/password updates), coach request workflow, calendar views, and all public pages.

---

## Project Structure

```
COEN6311-SANJ/
├── COEN6311/               # Django project config (settings, urls, wsgi)
├── CUFitness/              # Main application
│   ├── migrations/         # Database migrations
│   ├── static/             # CSS files
│   ├── templates/          # HTML templates
│   ├── models.py           # Database models
│   ├── views.py            # View logic
│   ├── urls.py             # URL routing
│   ├── forms.py            # Django forms
│   ├── managers.py         # Custom user manager
│   ├── admin.py            # Django admin config
│   └── tests.py            # Automated tests
├── db.sqlite3              # SQLite database
├── manage.py               # Django management CLI
├── seed_data.py            # Test data seeder
└── requirements.txt        # Python dependencies
```
