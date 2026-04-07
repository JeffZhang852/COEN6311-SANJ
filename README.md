# CUFitness

A Django web application for managing a university fitness centre. Members can browse services, request a coach, and manage their profile. Coaches manage their availability and appointments. Staff manage members, coach requests, and publish articles.

---

## Tech Stack

- **Backend:** Django 6.0.1, Django REST Framework 3.16.1
- **Database:** SQLite (via Django ORM)
- **Frontend:** HTML/CSS templates (Django template engine)
- **Auth:** Custom user model (`CustomUser`) with email-based login
- **AI Chatbot:** TinyLlama-1.1B-Chat (loaded via HuggingFace Transformers + PyTorch on startup)

---

## Prerequisites

- Python 3.10+
- pip

> **Note:** The AI chatbot (`TinyLlama/TinyLlama-1.1B-Chat-v1.0`) is downloaded from HuggingFace on first run. This requires an internet connection 
	and ~2 GB of disk space. The model loads in a background thread so the server starts immediately; chatbot responses will be unavailable for a short time after launch.

---

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/JeffZhang852/COEN6311-SANJ.git
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
> ```bash
>pip install -r requirements.txt
>```
> **Note:** `requirements.txt` is encoded as UTF-16. If `pip` fails to parse it, run this conversion first:
> ```bash
> python -c "open('req_utf8.txt','w').write(open('requirements.txt','rb').read().decode('utf-16'))"
> pip install -r req_utf8.txt
> ```
> Or install the core packages manually:
> ```bash
> pip install Django==6.0.1 djangorestframework django-filter django-multiselectfield pillow transformers torch accelerate
> 


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

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## Test Accounts

All accounts are created by `seed_data.py`.

| Role   | Email                 | Password    | Login URL       |
|--------|-----------------------|-------------|-----------------|
| Admin  | admin@cufitness.com   | Admin@1234  | `/admin/`       |
| Staff  | staff1@cufitness.com  | Staff@1234  | `/staff_login/` |
| Staff  | staff2@cufitness.com  | Staff@1234  | `/staff_login/` |
| Coach  | coach1@cufitness.com  | Coach@1234  | `/coach_login/` |
| Coach  | coach2@cufitness.com  | Coach@1234  | `/coach_login/` |
| Coach  | coach3@cufitness.com  | Coach@1234  | `/coach_login/` |
| Member | member1@cufitness.com | Member@1234 | `/login/`       |
| Member | member2@cufitness.com | Member@1234 | `/login/`       |
| Member | member3@cufitness.com | Member@1234 | `/login/`       |

> **Important:** Each role has a **separate login portal**. Members use `/login/`, coaches use `/coach_login/`, and staff use `/staff_login/`. Attempting to log in via the wrong portal will redirect you to the correct one.
>
> Admin users log in via the Django admin panel at `/admin/` only.

---

## User Roles

**Member**
Can browse public pages, manage their profile and privacy settings, request to become a coach, book coach appointments, track challenge progress, and message coaches.

**Coach**
Everything a member can do, plus: manage availability slots (including recurring weekly slots), accept/refuse appointment requests, view their schedule on a calendar, see their salary estimate, and view reviews from members.

**Staff**
Separate login portal. Can view and manage all members and coaches, handle coach role requests (approve/reject), publish and manage articles/recipes/exercises/workout plans/challenges, view contact messages, and access staff reports.

**Admin**
Superuser access via the Django admin panel at `/admin/`. Full control over all models and user management.

---

## Key URLs

### Public Pages

| URL | Description |
|-----|-------------|
| `/` | Home page (redirects coaches and staff to their dashboards) |
| `/services/` | Services and equipment overview |
| `/articles/` | Fitness/nutrition articles (free + premium) |
| `/recipes/` | Recipes (free + premium) |
| `/workout_plans/` | Workout plans (free + premium) |
| `/exercises/` | Exercise library |
| `/challenges/` | Fitness challenges (login required to join) |
| `/fitness_assistant/` | AI chatbot (TinyLlama) |
| `/amenities/` | Gym amenities |
| `/schedule/` | Gym operating hours |
| `/contact/` | Contact form |
| `/about/` | About page |
| `/faq/` | FAQ |
| `/privacy_policy/` | Privacy policy |

### Authentication

| URL | Description |
|-----|-------------|
| `/register/` | New member registration |
| `/login/` | Member login |
| `/coach_login/` | Coach login |
| `/staff_login/` | Staff login |
| `/logout/` | Logout (any role) |

### Member / Coach

| URL | Description |
|-----|-------------|
| `/user_profile/` | Profile page with appointment history |
| `/user_profile/upload_picture/` | Upload profile picture |
| `/user_profile/delete-picture/` | Delete profile picture |
| `/user_settings/` | Email, password, privacy settings, coach request |
| `/user_inbox/` | Inbox (member ↔ coach messaging) |
| `/user_calendar/` | Appointment calendar and booking |
| `/coach_home/` | Coach dashboard |
| `/coach_profile/` | Coach profile with reviews and salary estimate |
| `/coach_settings/` | Coach email and password settings |
| `/coach_schedule/` | Coach availability and appointment management |

### Staff

| URL | Description |
|-----|-------------|
| `/staff_profile/` | Staff profile |
| `/staff_settings/` | Staff password settings |
| `/staff_messages/` | View and manage contact form submissions |
| `/coach_requests/` | Approve/reject coach role requests |
| `/staff_reports/` | Reports page *(stub — not yet implemented)* |
| `/staff_user_details/<id>/` | Detailed view of a member or coach |
| `/staff_articles/` | Article management |
| `/staff_create_article/` | Create a new article |
| `/staff_recipes/` | Recipe management |
| `/staff_create_recipe/` | Create a new recipe |
| `/staff_workouts/` | Workout plan management |
| `/staff_create_workout/` | Create a new workout plan |
| `/staff_exercises/` | Exercise management |
| `/staff_create_exercise/` | Create a new exercise |
| `/staff_challenges/` | Challenge management |
| `/staff_create_challenge/` | Create a new challenge |

### REST API

| URL | Description |
|-----|-------------|
| `/api/` | DRF browsable API root |
| `/api/users/` | User list (staff only) |
| `/api/users/me/` | Current user's data |
| `/api/users/<id>/coach-profile/` | Coach profile, salary, and reviews |
| `/api/reviews/` | Coach review list/create |
| `/api/coaches/` | Active coach list (AJAX) |
| `/api/coach-availability/` | Coach availability for a date range |
| `/api/all-availability/` | All coaches' availability for a date |
| `/api/request-appointment/` | Book an appointment (POST) |
| `/api/appointment/<id>/accept/` | Coach accepts appointment |
| `/api/appointment/<id>/reject/` | Coach rejects appointment |
| `/api/appointment/<id>/cancel/` | Member cancels appointment |
| `/api/availability/add/` | Coach adds availability slot(s) |
| `/api/availability/<id>/edit/` | Coach edits an availability slot |
| `/api/availability/<id>/delete/` | Coach deletes an availability slot |
| `/api/availability/<uuid>/cancel_series/` | Coach cancels a recurring series |
| `/api/coaches/search/` | Member searches for a coach by name |

---

## Database Models

**CustomUser** — extends `AbstractBaseUser`. Fields: `email` (login field), `first_name`, `last_name`, `role` (MEMBER / COACH / STAFF / ADMIN), `membership` (BASIC / STANDARD / PLATINUM / PER_SESSION), `phone_number`, `date_of_birth`, `address`, `profile_picture`, `coach_request_status` (NONE / PENDING / APPROVED / REJECTED), `workout_visibility` (PUBLIC / COACH_ONLY). `is_staff` is automatically synced from `role` on save.

**Article** — fitness/nutrition articles published by staff. Has a `locked` flag for premium content visible only to authenticated users.

**EquipmentList** — gym equipment items with quantity and an `is_active` flag for out-of-service status.

**Recipe** — recipes with ingredients, dietary restriction tags, difficulty, and a `locked` flag. Supports prep/cook time and calorie information.

**RecipeIngredient** — individual ingredients linked to a recipe via inline formset. Supports multiple unit types.

**Exercise** — exercise entries with muscle group, difficulty, goal, and linked equipment (M2M).

**WorkoutPlan** — ordered collection of exercises forming a complete routine. Has a `locked` flag for premium content.

**WorkoutPlanExercise** — through model linking exercises to workout plans with sets/reps/rest/order fields.

**Challenge** — fitness challenges created by staff with a goal target and date range.

**ChallengeParticipation** — tracks a member's progress toward a challenge goal. One participation per user per challenge enforced at the database level.

**GymInfo** — operating hours per day of the week. Supports 24-hour days and closed days.

**CoachAvailability** — time slots a coach marks as open. Validates non-overlapping slots. Supports recurring weekly series grouped by UUID. Prevents deletion of booked slots.

**CoachAppointment** — a member's booking of a coach's availability slot. Statuses: PENDING / ACCEPTED / REFUSED / CANCELLED. Prevents double-booking via model-level validation. Booking uses a database-level atomic transaction to prevent race conditions.

**CoachReview** — one review per appointment. Rating 1–5 stars with optional comment. Only members with an accepted/refused appointment can leave a review.

**Message** — direct messages between members and coaches.

**ContactMessage** — support messages submitted via the public contact form. Visible to all staff.

---

## Running Tests

```bash
python manage.py test CUFitness
```

The test suite covers model validation, authentication, access control, article/recipe/workout CRUD, settings (email/password updates), coach request workflow, calendar views, appointment booking flow, and all public pages.

---

## Project Structure

```
COEN6311-SANJ/
├── COEN6311/               # Django project config
│   ├── settings.py         # Project settings
│   ├── urls.py             # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
├── CUFitness/              # Main application
│   ├── migrations/         # Database migrations
│   ├── static/             # CSS files (per-role: general, staff, user, coach)
│   ├── templates/          # HTML templates (per-role subdirectories)
│   ├── models.py           # All database models
│   ├── views.py            # All view logic (general, user, coach, staff, API)
│   ├── urls.py             # App-level URL routing
│   ├── forms.py            # Django forms
│   ├── managers.py         # Custom user manager (email-based auth)
│   ├── serializers.py      # DRF serializers
│   ├── admin.py            # Django admin configuration
│   ├── apps.py             # App config + background chatbot model loader
│   └── tests.py            # Automated test suite
├── media/                  # User-uploaded files (profile pictures)
│   └── defaults/           # Default profile picture
├── db.sqlite3              # SQLite database (pre-seeded by seed_data.py)
├── manage.py               # Django management CLI
├── seed_data.py            # Test data seeder
├── requirements.txt        # Python dependencies (UTF-16 encoded — see Setup)
└── CHANGELOG.md            # Project changelog
```