"""
seed_data.py — CUFitness Database Seeder
=========================================
this file creates testing data for both user accounts (admin, staff, coach) and article data (locked/unlocked
What it creates:
  - 1 Admin user        (admin@cufitness.com  / Admin@1234)
  - 2 Staff users       (staff1@..., staff2@... / Staff@1234)
  - 3 Regular members   (member1@..., member2@..., member3@... / Member@1234)
  - 5 Articles          (3 unlocked, 2 locked), authored by the staff users

All entries are idempotent — re-running won't duplicate data.
"""

import django
import os

# Only needed when running as a standalone script (not via manage.py shell)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "COEN6311.settings")
django.setup()

from django.contrib.auth import get_user_model
from CUFitness.models import Articles

User = get_user_model()

# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def create_user(email, password, first_name, last_name,
                role, membership="BASIC", is_staff_flag=False, is_superuser=False):
    if User.objects.filter(email=email).exists():
        print(f"  [skip] User already exists: {email}")
        return User.objects.get(email=email)

    if is_superuser:
        user = User.objects.create_superuser(email=email, password=password)
    else:
        user = User.objects.create_user(email=email, password=password)

    user.first_name = first_name
    user.last_name  = last_name
    user.role       = role
    user.membership = membership
    user.is_staff   = is_staff_flag
    user.save()
    print(f"  [created] {role}: {email}")
    return user


def create_article(author, title, description, body, locked):
    if Articles.objects.filter(title=title).exists():
        print(f"  [skip] Article already exists: '{title}'")
        return Articles.objects.get(title=title)

    article = Articles.objects.create(
        author=author,
        title=title,
        description=description,
        body=body,
        locked=locked,
    )
    status = "🔒 locked" if locked else "🔓 unlocked"
    print(f"  [created] Article ({status}): '{title}'")
    return article


# ─────────────────────────────────────────────
# 1. Admin
# ─────────────────────────────────────────────
print("\n── Creating Admin ──")
admin = create_user(
    email        = "admin@cufitness.com",
    password     = "Admin@1234",
    first_name   = "Admin",
    last_name    = "User",
    role         = "ADMIN",
    is_staff_flag= True,
    is_superuser = True,
)

# ─────────────────────────────────────────────
# 2. Staff Users
# ─────────────────────────────────────────────
print("\n── Creating Staff Users ──")
staff1 = create_user(
    email        = "staff1@cufitness.com",
    password     = "Staff@1234",
    first_name   = "Sarah",
    last_name    = "Connor",
    role         = "STAFF",
    is_staff_flag= True,
)

staff2 = create_user(
    email        = "staff2@cufitness.com",
    password     = "Staff@1234",
    first_name   = "James",
    last_name    = "Wilson",
    role         = "STAFF",
    is_staff_flag= True,
)

# ─────────────────────────────────────────────
# 3. Regular Members
# ─────────────────────────────────────────────
print("\n── Creating Regular Members ──")
member1 = create_user(
    email      = "member1@cufitness.com",
    password   = "Member@1234",
    first_name = "Alice",
    last_name  = "Johnson",
    role       = "MEMBER",
    membership = "BASIC",
)

member2 = create_user(
    email      = "member2@cufitness.com",
    password   = "Member@1234",
    first_name = "Bob",
    last_name  = "Martinez",
    role       = "MEMBER",
    membership = "STANDARD",
)

member3 = create_user(
    email      = "member3@cufitness.com",
    password   = "Member@1234",
    first_name = "Carol",
    last_name  = "Davis",
    role       = "MEMBER",
    membership = "PLATINUM",
)

# ─────────────────────────────────────────────
# 4. Coach User
# ─────────────────────────────────────────────
print("\n── Creating Coach ──")
coach = create_user(
    email        = "coach1@cufitness.com",
    password     = "Coach@1234",
    first_name   = "Mike",
    last_name    = "Thompson",
    role         = "COACH",
    membership   = "BASIC",
)

# ─────────────────────────────────────────────
# 5. Articles (authored by staff)
# ─────────────────────────────────────────────
print("\n── Creating Articles ──")

create_article(
    author      = staff1,
    title       = "5 Best Warm-Up Exercises Before Any Workout",
    description = "A quick guide to effective warm-up routines that prevent injury.",
    body        = (
        "Warming up before exercise is essential to prepare your muscles and joints. "
        "Here are five exercises everyone should do:\n\n"
        "1. Jumping Jacks (2 minutes) — gets your heart rate up.\n"
        "2. Arm Circles — loosens shoulder joints.\n"
        "3. Hip Rotations — preps the hip flexors.\n"
        "4. Leg Swings — activates hamstrings and quads.\n"
        "5. High Knees (30 seconds) — full-body activation.\n\n"
        "Always spend at least 5–10 minutes warming up before intense activity."
    ),
    locked      = False,
)

create_article(
    author      = staff1,
    title       = "Understanding Macronutrients: Protein, Carbs & Fats",
    description = "Learn what macronutrients are and how to balance them in your diet.",
    body        = (
        "Macronutrients are the three main categories of nutrients that fuel your body:\n\n"
        "**Protein** (4 kcal/g): Builds and repairs muscle tissue. Aim for 0.8–1.2g per kg of body weight.\n\n"
        "**Carbohydrates** (4 kcal/g): Your body's primary energy source. Choose complex carbs like oats, "
        "sweet potatoes, and whole grains over simple sugars.\n\n"
        "**Fats** (9 kcal/g): Essential for hormones and vitamin absorption. Focus on healthy fats from "
        "avocados, nuts, and olive oil.\n\n"
        "A balanced plate typically contains 40% carbs, 30% protein, and 30% fat — but this varies "
        "based on your fitness goals."
    ),
    locked      = False,
)

create_article(
    author      = staff2,
    title       = "Beginner's Guide to Strength Training",
    description = "Everything a beginner needs to know to start lifting safely and effectively.",
    body        = (
        "Starting strength training can feel overwhelming, but it doesn't have to be.\n\n"
        "**Start with compound movements**: Squats, deadlifts, bench press, and rows give you the most "
        "benefit per exercise.\n\n"
        "**Use proper form first**: Always prioritize technique over heavy weight. Poor form leads to injury.\n\n"
        "**Progressive overload**: Gradually increase weight or reps each week to keep making progress.\n\n"
        "**Rest days matter**: Muscles grow during rest, not during the workout. Allow 48 hours between "
        "training the same muscle group.\n\n"
        "A simple 3-day/week full-body routine is perfect for beginners."
    ),
    locked      = False,
)

create_article(
    author      = staff2,
    title       = "Advanced HIIT Protocols for Maximum Fat Loss",
    description = "Premium high-intensity interval training plans designed for experienced athletes.",
    body        = (
        "High-Intensity Interval Training (HIIT) at an advanced level requires careful programming "
        "to maximize results while avoiding overtraining.\n\n"
        "**Protocol 1 — Tabata**: 20 seconds all-out effort, 10 seconds rest, 8 rounds per exercise.\n\n"
        "**Protocol 2 — 30/30**: 30 seconds sprint, 30 seconds walk, repeated for 20 minutes.\n\n"
        "**Protocol 3 — Pyramid**: Intervals increase from 20s → 40s → 60s → 40s → 20s with equal rest.\n\n"
        "For maximum fat oxidation, perform HIIT in a fasted state or 2+ hours post-meal. "
        "Limit sessions to 3x/week to allow full recovery. Pair with adequate protein intake (1.6g/kg) "
        "to preserve lean muscle mass."
    ),
    locked      = True,   # Premium content
)

create_article(
    author      = staff1,
    title       = "Personalized Meal Planning: A Step-by-Step System",
    description = "A detailed premium guide to building a sustainable meal plan tailored to your goals.",
    body        = (
        "Building a personalized meal plan is the single most impactful nutrition change you can make.\n\n"
        "**Step 1 — Calculate your TDEE**: Total Daily Energy Expenditure is your maintenance calorie number. "
        "Use the Mifflin-St Jeor equation as a baseline.\n\n"
        "**Step 2 — Set your goal deficit or surplus**:\n"
        "  - Fat loss: subtract 300–500 kcal from TDEE\n"
        "  - Muscle gain: add 200–300 kcal to TDEE\n\n"
        "**Step 3 — Distribute your macros**: Set protein first (1g per lb of lean body mass), "
        "then fill remaining calories with carbs and fats based on preference.\n\n"
        "**Step 4 — Meal prep Sunday**: Cook proteins and grains in bulk to make weekday eating effortless.\n\n"
        "**Step 5 — Track and adjust**: Use a food diary for 2 weeks, then adjust portions if the scale "
        "isn't moving in the right direction.\n\n"
        "This system is included in the Platinum and Standard membership tiers."
    ),
    locked      = True,   # Premium content
)

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("\n" + "="*50)
print("✅ Seed complete! Summary:")
print(f"   Users  : {User.objects.count()} total")
print(f"   Articles: {Articles.objects.count()} total")
print()
print("Login credentials:")
print("  Admin  : admin@cufitness.com   / Admin@1234")
print("  Staff  : staff1@cufitness.com  / Staff@1234")
print("           staff2@cufitness.com  / Staff@1234")
print("  Members: member1@cufitness.com / Member@1234")
print("           member2@cufitness.com / Member@1234")
print("           member3@cufitness.com / Member@1234")
print("  Coach  : coach1@cufitness.com  / Coach@1234")
print("="*50)
