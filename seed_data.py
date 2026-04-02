"""
seed_data.py — CUFitness Database Seeder
=========================================
this file creates testing data for both user accounts (admin, staff, coach) and article data (locked/unlocked
What it creates:
  - 1 Admin user        (admin@cufitness.com  / Admin@1234)
  - 2 Staff users       (staff1@..., staff2@... / Staff@1234)
  - 3 Regular members   (member1@..., member2@..., member3@... / Member@1234)
  - 5 Articles          (3 unlocked, 2 locked), authored by the staff users
  - 6 Recipes           (4 unlocked, 2 locked), with ingredients, authored by staff/coach

All entries are idempotent — re-running won't duplicate data.
"""

import django
import os

# Only needed when running as a standalone script (not via manage.py shell)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "COEN6311.settings")
django.setup()

from django.contrib.auth import get_user_model
from CUFitness.models import (Article, Recipe, RecipeIngredient, Exercise, WorkoutPlan, WorkoutPlanExercise,
                              EquipmentList, Challenge, GymInfo)

from django.utils import timezone
from datetime import datetime, time

User = get_user_model()

# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def create_user(email, password, first_name, last_name,
                role, membership="BASIC", is_staff_flag=False, is_superuser=False,
                phone_number='', address='', date_of_birth=None):
    if User.objects.filter(email=email).exists():
        print(f"  [skip] User already exists: {email}")
        return User.objects.get(email=email)

    if is_superuser:
        user = User.objects.create_superuser(email=email, password=password)
    else:
        user = User.objects.create_user(email=email, password=password)

    user.first_name    = first_name
    user.last_name     = last_name
    user.role          = role
    user.membership    = membership
    user.is_staff      = is_staff_flag
    user.phone_number  = phone_number
    user.address       = address
    user.date_of_birth = date_of_birth
    if role == 'COACH':
        user.coach_request_status = 'APPROVED'
    user.save()
    print(f"  [created] {role}: {email}")
    return user


def create_article(author, title, description, body, locked):
    if Article.objects.filter(title=title).exists():
        print(f"  [skip] Article already exists: '{title}'")
        return Article.objects.get(title=title)

    article = Article.objects.create(
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
    email          = "admin@cufitness.com",
    password       = "Admin@1234",
    first_name     = "Admin",
    last_name      = "User",
    role           = "ADMIN",
    is_staff_flag  = True,
    is_superuser   = True,
    phone_number   = "+1 514 900 0001",
    address        = "1455 De Maisonneuve Blvd W, Montreal, QC H3G 1M8",
    date_of_birth  = "1980-01-15",
)

# ─────────────────────────────────────────────
# 2. Staff Users
# ─────────────────────────────────────────────
print("\n── Creating Staff Users ──")
staff1 = create_user(
    email          = "staff1@cufitness.com",
    password       = "Staff@1234",
    first_name     = "Sarah",
    last_name      = "Connor",
    role           = "STAFF",
    is_staff_flag  = True,
    phone_number   = "+1 514 900 0002",
    address        = "4121 Sherbrooke St W, Westmount, QC H3Z 1B5",
    date_of_birth  = "1990-03-22",
)

staff2 = create_user(
    email          = "staff2@cufitness.com",
    password       = "Staff@1234",
    first_name     = "James",
    last_name      = "Wilson",
    role           = "STAFF",
    is_staff_flag  = True,
    phone_number   = "+1 514 900 0003",
    address        = "7005 Taschereau Blvd, Brossard, QC J4Z 1A7",
    date_of_birth  = "1988-07-09",
)

# ─────────────────────────────────────────────
# 3. Regular Members
# ─────────────────────────────────────────────
print("\n── Creating Regular Members ──")
member1 = create_user(
    email          = "member1@cufitness.com",
    password       = "Member@1234",
    first_name     = "Alice",
    last_name      = "Johnson",
    role           = "MEMBER",
    membership     = "BASIC",
    phone_number   = "+1 514 900 0004",
    address        = "3480 Rue University, Montreal, QC H3A 2A7",
    date_of_birth  = "1998-11-30",
)

member2 = create_user(
    email          = "member2@cufitness.com",
    password       = "Member@1234",
    first_name     = "Bob",
    last_name      = "Martinez",
    role           = "MEMBER",
    membership     = "STANDARD",
    phone_number   = "+1 514 900 0005",
    address        = "1600 Lapointe St, Longueuil, QC J4K 2K1",
    date_of_birth  = "1995-05-14",
)

member3 = create_user(
    email          = "member3@cufitness.com",
    password       = "Member@1234",
    first_name     = "Carol",
    last_name      = "Davis",
    role           = "MEMBER",
    membership     = "PLATINUM",
    phone_number   = "+1 514 900 0006",
    address        = "900 Boulevard de Maisonneuve E, Montreal, QC H2L 1Y8",
    date_of_birth  = "2000-02-28",
)

# ─────────────────────────────────────────────
# 4. Coach User
# ─────────────────────────────────────────────
print("\n── Creating Coach ──")
coach1 = create_user(
    email          = "coach1@cufitness.com",
    password       = "Coach@1234",
    first_name     = "Mike",
    last_name      = "Thompson",
    role           = "COACH",
    membership     = "BASIC",
    phone_number   = "+1 514 900 0007",
    address        = "5757 Decarie Blvd, Montreal, QC H3X 3L3",
    date_of_birth  = "1985-09-03",
)

coach2 = create_user(
    email          = "coach2@cufitness.com",
    password       = "Coach@1234",
    first_name     = "George",
    last_name      = "Thompson",
    role           = "COACH",
    membership     = "BASIC",
    phone_number   = "+1 514 900 0008",
    address        = "5757 Decarie Blvd, Montreal, QC H3X 3L3",
    date_of_birth  = "1985-09-03",
)

coach3 = create_user(
    email          = "coach3@cufitness.com",
    password       = "Coach@1234",
    first_name     = "Sarah",
    last_name      = "Thompson",
    role           = "COACH",
    membership     = "BASIC",
    phone_number   = "+1 514 900 0009",
    address        = "5757 Decarie Blvd, Montreal, QC H3X 3L3",
    date_of_birth  = "1985-09-03",
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

create_article(
    author      = staff2,
    title       = "The Science of Sleep & Athletic Recovery",
    description = "Why sleep is the most underrated performance tool and how to optimise it.",
    body        = (
        "Most athletes obsess over training and nutrition but neglect the single most powerful recovery tool available: sleep.\n\n"
        "**What happens during sleep**: Growth hormone secretion peaks during deep sleep stages, driving muscle repair and tissue regeneration. "
        "Memory consolidation during REM sleep also improves motor skill learning — meaning technique practice is literally processed overnight.\n\n"
        "**How much do you need?**: Recreational athletes should target 7–9 hours. Elite and high-volume athletes often benefit from 9–10 hours. "
        "Even one night of poor sleep (under 6 hours) measurably reduces reaction time, strength output, and aerobic capacity.\n\n"
        "**Practical tips**:\n"
        "- Keep a consistent sleep/wake schedule — even on weekends\n"
        "- Avoid screens for 60 minutes before bed (blue light suppresses melatonin)\n"
        "- Keep your room cool (16–19°C is optimal for sleep)\n"
        "- Avoid caffeine after 2pm\n"
        "- Consider magnesium glycinate (200–400mg) before bed to support relaxation\n\n"
        "Treat sleep with the same intentionality as your training sessions and your recovery will improve dramatically."
    ),
    locked      = False,
)

create_article(
    author      = staff1,
    title       = "How to Prevent the 5 Most Common Gym Injuries",
    description = "Practical prevention strategies for the injuries that sideline most gym-goers.",
    body        = (
        "Injuries don't just happen — they're almost always the result of predictable, avoidable mistakes. "
        "Here are the five most common gym injuries and exactly how to prevent them.\n\n"
        "**1. Lower Back Strain**\nCause: Rounding the lower back during deadlifts and rows.\n"
        "Fix: Brace your core before every rep, hinge from the hips, and never load a fatigued back.\n\n"
        "**2. Shoulder Impingement**\nCause: Excessive internal rotation, poor posture, and skipping rear delt/rotator cuff work.\n"
        "Fix: Add face pulls and band pull-aparts to every upper body session. Fix your desk posture.\n\n"
        "**3. Knee Pain (Patellar Tendinopathy)**\nCause: Rapid training load increases, poor squat mechanics.\n"
        "Fix: Follow the 10% rule — increase weekly training load by no more than 10% per week. "
        "Ensure knees track over toes in all leg exercises.\n\n"
        "**4. Bicep Tendon Strain**\nCause: Heavy curls with supinated grip at the bottom, poor warm-up.\n"
        "Fix: Always warm up with light resistance before heavy curls. Avoid extreme stretching under load.\n\n"
        "**5. Wrist Pain**\nCause: Incorrect bar position in pressing movements, weak wrist flexors.\n"
        "Fix: Keep wrists neutral and stacked over elbows. Add wrist curls and extensions to accessory work.\n\n"
        "Prevention is always better than rehab. A 5-minute prehab routine before each session is an investment that pays for itself."
    ),
    locked      = False,
)

create_article(
    author      = staff2,
    title       = "Creatine: What the Research Actually Says",
    description = "An evidence-based breakdown of the most studied supplement in sports science.",
    body        = (
        "Creatine monohydrate is the single most researched and most effective legal performance supplement available. "
        "Here's what the science actually shows — without the marketing hype.\n\n"
        "**What it does**: Creatine increases phosphocreatine stores in your muscles, allowing faster regeneration of ATP "
        "(your primary energy currency) during high-intensity efforts lasting 1–30 seconds.\n\n"
        "**Proven benefits**:\n"
        "- Increases maximal strength output (average: 5–15%)\n"
        "- Improves repeated sprint performance\n"
        "- Supports lean muscle gain when combined with resistance training\n"
        "- Emerging evidence suggests cognitive and neuroprotective benefits\n\n"
        "**Dosing protocol**: There are two approaches:\n"
        "- Loading: 20g/day split into 4 doses for 5–7 days, then 3–5g/day maintenance\n"
        "- No loading: 3–5g/day from the start (reaches saturation in ~4 weeks)\n\n"
        "**Safety**: Creatine monohydrate is safe for healthy adults at recommended doses. "
        "Claims that it damages kidneys are not supported by research in healthy individuals. "
        "Drink adequate water as creatine draws fluid into muscle cells.\n\n"
        "**Form to buy**: Plain creatine monohydrate. Not creatine HCl, ethyl ester, or any 'advanced' variant — "
        "none of these have been shown to outperform plain monohydrate at equivalent doses."
    ),
    locked      = False,
)

create_article(
    author      = staff1,
    title       = "Mental Toughness: Building a Resilient Athletic Mindset",
    description = "Psychological tools used by elite athletes to push through discomfort and stay consistent.",
    body        = (
        "Physical capacity is only half the equation. What separates consistent athletes from inconsistent ones "
        "is almost always psychological, not physiological.\n\n"
        "**1. Reframe discomfort as signal, not threat**\nElite athletes learn to interpret the burning sensation of hard effort "
        "as confirmation that training is working — not as a reason to stop. Practice labelling discomfort neutrally: "
        "'This is hard' rather than 'This is too hard.'\n\n"
        "**2. Use process goals, not outcome goals**\nInstead of 'I want to bench 100kg', set 'I will hit every scheduled session this month.' "
        "Outcomes follow from consistent process. Focusing on outcomes creates anxiety; focusing on process creates action.\n\n"
        "**3. Visualisation**\nMental rehearsal activates the same motor pathways as physical practice. "
        "Spend 5 minutes before each session mentally rehearsing your key movements performed perfectly.\n\n"
        "**4. Identity-based habits**\nInstead of 'I'm trying to be fit,' adopt 'I am someone who trains.' "
        "Identity-level beliefs are far more powerful drivers of behaviour than motivation alone.\n\n"
        "**5. Control the controllables**\nYou cannot control whether you get injured, whether the gym is busy, "
        "or whether progress is fast. You can control your effort, your preparation, and your consistency. "
        "Direct all mental energy toward what's in your control."
    ),
    locked      = False,
)

create_article(
    author      = staff2,
    title       = "Periodisation for Intermediate Athletes: How to Structure Your Year",
    description = "A premium guide to annual training planning using proven periodisation models.",
    body        = (
        "Once you've been training consistently for 1–2 years, random programming stops working. "
        "Progress requires deliberate periodisation — the planned variation of training stress over time.\n\n"
        "**Why periodisation?**: Your body adapts to any fixed stimulus within 4–8 weeks. "
        "Periodisation prevents adaptation plateaus, manages fatigue, and peaks performance at the right time.\n\n"
        "**Linear Periodisation** (best for beginners moving to intermediate):\n"
        "Progressively increase load each week for 4–6 weeks, then deload for 1 week. Simple and effective.\n\n"
        "**Block Periodisation** (for intermediate to advanced):\n"
        "Train in focused 3–6 week blocks with a single primary goal:\n"
        "- Accumulation block: high volume, moderate intensity (hypertrophy focus)\n"
        "- Intensification block: moderate volume, high intensity (strength focus)\n"
        "- Realisation block: low volume, peak intensity (performance expression)\n\n"
        "**Undulating Periodisation**:\n"
        "Vary training stimulus daily or weekly (e.g. Monday: strength, Wednesday: hypertrophy, Friday: power). "
        "Excellent for athletes who train 3–4 days/week and want variety.\n\n"
        "**Practical starting point**: Run 3 accumulation weeks → 1 deload → 3 intensification weeks → 1 deload → test your lifts. "
        "This 8-week mini-cycle is a reliable framework for continuous progress.\n\n"
        "This guide is part of the CUFitness Premium coaching programme."
    ),
    locked      = True,
)

# ─────────────────────────────────────────────
# 6. Recipes (authored by staff & coach)
# ─────────────────────────────────────────────

def create_recipe(author, title, description, difficulty,
                  prep, cook, servings, calories, dietary, locked, instructions, ingredients):
    if Recipe.objects.filter(title=title).exists():
        print(f"  [skip] Recipe already exists: '{title}'")
        return Recipe.objects.get(title=title)

    recipe = Recipe.objects.create(
        author               = author,
        title                = title,
        description          = description,
        difficulty           = difficulty,
        prep_time_minutes    = prep,
        cook_time_minutes    = cook,
        servings             = servings,
        calories_per_serving = calories,
        dietary_restrictions      = dietary,
        locked               = locked,
        instructions         = instructions,
    )

    for ing in ingredients:
        RecipeIngredient.objects.create(
            recipe   = recipe,
            name     = ing['name'],
            quantity = ing['quantity'],
            unit     = ing['unit'],
            notes    = ing.get('notes', ''),
        )

    status = "🔒 locked" if locked else "🔓 unlocked"
    print(f"  [created] Recipe ({status}): '{title}'")
    return recipe


print("\n── Creating Recipes ──")

create_recipe(
    author      = staff1,
    title       = "High-Protein Chicken & Quinoa Bowl",
    description = "A quick post-workout meal packed with lean protein and complex carbs.",
    difficulty  = "EASY",
    prep        = 10,
    cook        = 20,
    servings    = 2,
    calories    = 480,
    dietary     = ['NO_GLUTEN', 'NO_DAIRY_LACTOSE'],
    locked      = False,
    instructions = (
        "1. Rinse quinoa under cold water and cook in chicken broth (1:2 ratio) for 15 minutes.\n"
        "2. Season chicken breast with salt, pepper, and garlic powder.\n"
        "3. Heat olive oil in a pan over medium-high heat. Cook chicken 6–7 minutes per side until golden.\n"
        "4. Rest chicken for 5 minutes then slice.\n"
        "5. Divide quinoa between bowls, top with sliced chicken, cherry tomatoes, and cucumber.\n"
        "6. Drizzle with lemon juice and serve."
    ),
    ingredients = [
        {'name': 'chicken breast',    'quantity': '300', 'unit': 'G'},
        {'name': 'quinoa',            'quantity': '1',   'unit': 'CUP'},
        {'name': 'chicken broth',     'quantity': '2',   'unit': 'CUP'},
        {'name': 'olive oil',         'quantity': '1',   'unit': 'TBSP'},
        {'name': 'cherry tomatoes',   'quantity': '100', 'unit': 'G',    'notes': 'halved'},
        {'name': 'cucumber',          'quantity': '0.5', 'unit': 'WHOLE','notes': 'diced'},
        {'name': 'lemon juice',       'quantity': '2',   'unit': 'TBSP'},
        {'name': 'garlic powder',     'quantity': '1',   'unit': 'TSP'},
    ],
)

create_recipe(
    author      = staff2,
    title       = "Overnight Oats with Berries",
    description = "No-cook, prep-ahead breakfast loaded with fibre and antioxidants.",
    difficulty  = "EASY",
    prep        = 5,
    cook        = 0,
    servings    = 1,
    calories    = 350,
    dietary     = ['NO_NUTS', 'VEGETARIAN'],
    locked      = False,
    instructions = (
        "1. Add oats, chia seeds, and milk to a jar or container with a lid.\n"
        "2. Stir in honey and vanilla extract.\n"
        "3. Seal and refrigerate overnight (at least 6 hours).\n"
        "4. In the morning, top with Greek yogurt and mixed berries.\n"
        "5. Stir and eat cold, or microwave for 90 seconds if you prefer it warm."
    ),
    ingredients = [
        {'name': 'rolled oats',    'quantity': '0.5', 'unit': 'CUP'},
        {'name': 'chia seeds',     'quantity': '1',   'unit': 'TBSP'},
        {'name': 'milk',           'quantity': '0.5', 'unit': 'CUP',  'notes': 'dairy or plant-based'},
        {'name': 'Greek yogurt',   'quantity': '100', 'unit': 'G'},
        {'name': 'mixed berries',  'quantity': '80',  'unit': 'G',    'notes': 'fresh or frozen'},
        {'name': 'honey',          'quantity': '1',   'unit': 'TSP'},
        {'name': 'vanilla extract','quantity': '0.5', 'unit': 'TSP'},
    ],
)

create_recipe(
    author      = coach2,
    title       = "Lean Turkey Meatballs with Zoodles",
    description = "Low-carb, high-protein dinner that's easy to batch cook for the week.",
    difficulty  = "MEDIUM",
    prep        = 15,
    cook        = 25,
    servings    = 4,
    calories    = 320,
    dietary     = ['NO_GLUTEN', 'NO_DAIRY_LACTOSE'],
    locked      = False,
    instructions = (
        "1. Preheat oven to 200°C (400°F). Line a baking tray with parchment paper.\n"
        "2. Mix turkey mince with egg, garlic, parsley, salt, and pepper. Roll into 16 equal balls.\n"
        "3. Bake meatballs for 20–22 minutes until cooked through.\n"
        "4. Meanwhile, spiralize zucchini into noodles. Sauté in olive oil for 2–3 minutes — don't overcook.\n"
        "5. Warm marinara sauce in a saucepan.\n"
        "6. Plate zoodles, top with meatballs, and spoon over sauce. Garnish with fresh basil."
    ),
    ingredients = [
        {'name': 'turkey mince',    'quantity': '500', 'unit': 'G'},
        {'name': 'egg',             'quantity': '1',   'unit': ''},
        {'name': 'garlic',          'quantity': '2',   'unit': '',    'notes': 'cloves, minced'},
        {'name': 'fresh parsley',   'quantity': '2',   'unit': 'TBSP','notes': 'chopped'},
        {'name': 'zucchini',        'quantity': '3',   'unit': 'WHOLE','notes': 'spiralized'},
        {'name': 'olive oil',       'quantity': '1',   'unit': 'TBSP'},
        {'name': 'marinara sauce',  'quantity': '1.5', 'unit': 'CUP', 'notes': 'store-bought or homemade'},
        {'name': 'fresh basil',     'quantity': '1',   'unit': 'PINCH','notes': 'to garnish'},
    ],
)

create_recipe(
    author      = staff1,
    title       = "Vegan Black Bean Tacos",
    description = "Flavourful plant-based tacos ready in under 20 minutes.",
    difficulty  = "EASY",
    prep        = 10,
    cook        = 10,
    servings    = 2,
    calories    = 410,
    dietary     = ['VEGAN', 'NO_DAIRY_LACTOSE', 'NO_SEAFOOD'],
    locked      = False,
    instructions = (
        "1. Drain and rinse black beans. Heat in a pan with cumin, smoked paprika, and a pinch of salt for 3–4 minutes.\n"
        "2. Warm corn tortillas directly on a gas flame or dry pan for 30 seconds each side.\n"
        "3. Mash avocado with lime juice and salt to make a quick guacamole.\n"
        "4. Assemble tacos: spread guacamole, spoon over beans, top with salsa, red onion, and coriander.\n"
        "5. Serve immediately with lime wedges."
    ),
    ingredients = [
        {'name': 'black beans',     'quantity': '400', 'unit': 'G',    'notes': '1 can, drained'},
        {'name': 'corn tortillas',  'quantity': '4',   'unit': ''},
        {'name': 'avocado',         'quantity': '1',   'unit': 'WHOLE'},
        {'name': 'lime',            'quantity': '1',   'unit': 'WHOLE','notes': 'juiced'},
        {'name': 'salsa',           'quantity': '4',   'unit': 'TBSP'},
        {'name': 'red onion',       'quantity': '0.25','unit': 'WHOLE','notes': 'finely diced'},
        {'name': 'fresh coriander', 'quantity': '1',   'unit': 'PINCH'},
        {'name': 'cumin',           'quantity': '1',   'unit': 'TSP'},
        {'name': 'smoked paprika',  'quantity': '0.5', 'unit': 'TSP'},
    ],
)

create_recipe(
    author      = coach2,
    title       = "Athlete's Salmon & Sweet Potato Power Plate",
    description = "Premium performance meal optimised for muscle recovery and sustained energy.",
    difficulty  = "MEDIUM",
    prep        = 10,
    cook        = 30,
    servings    = 2,
    calories    = 620,
    dietary     = ['NO_GLUTEN', 'NO_DAIRY_LACTOSE'],
    locked      = True,   # Premium content
    instructions = (
        "1. Preheat oven to 200°C (400°F). Cube sweet potatoes and toss with olive oil, salt, and paprika.\n"
        "2. Roast sweet potatoes for 25–30 minutes, flipping halfway, until caramelised.\n"
        "3. Pat salmon fillets dry. Season with salt, pepper, and garlic.\n"
        "4. Heat a non-stick pan over high heat. Sear salmon skin-side up for 3 minutes, flip and cook 2 more minutes.\n"
        "5. Steam broccoli for 4–5 minutes until just tender.\n"
        "6. Plate sweet potato, broccoli, and salmon. Drizzle with tahini thinned with lemon juice and water."
    ),
    ingredients = [
        {'name': 'salmon fillet',   'quantity': '300', 'unit': 'G',    'notes': '2 fillets, skin-on'},
        {'name': 'sweet potato',    'quantity': '400', 'unit': 'G',    'notes': 'cubed'},
        {'name': 'broccoli',        'quantity': '200', 'unit': 'G',    'notes': 'cut into florets'},
        {'name': 'olive oil',       'quantity': '2',   'unit': 'TBSP'},
        {'name': 'tahini',          'quantity': '2',   'unit': 'TBSP'},
        {'name': 'lemon juice',     'quantity': '1',   'unit': 'TBSP'},
        {'name': 'garlic',          'quantity': '1',   'unit': '',     'notes': 'clove, minced'},
        {'name': 'smoked paprika',  'quantity': '1',   'unit': 'TSP'},
    ],
)

create_recipe(
    author      = staff2,
    title       = "Elite Bulking Beef & Rice Bowl",
    description = "Premium high-calorie mass-gain meal for serious athletes in a caloric surplus.",
    difficulty  = "MEDIUM",
    prep        = 10,
    cook        = 25,
    servings    = 2,
    calories    = 850,
    dietary     = ['NO_GLUTEN', 'NO_DAIRY_LACTOSE'],
    locked      = True,   # Premium content
    instructions = (
        "1. Cook jasmine rice according to package instructions.\n"
        "2. Brown beef mince in a hot pan over high heat — don't stir too often, let it get a crust.\n"
        "3. Add soy sauce (use tamari for gluten-free), sesame oil, ginger, and garlic. Cook 2 minutes.\n"
        "4. Stir in edamame and cook 1 more minute.\n"
        "5. Fry eggs sunny-side up in a separate pan.\n"
        "6. Serve beef mixture over rice, topped with a fried egg, sliced spring onion, and sesame seeds."
    ),
    ingredients = [
        {'name': 'beef mince',      'quantity': '400', 'unit': 'G',    'notes': 'lean, 5% fat'},
        {'name': 'jasmine rice',    'quantity': '1.5', 'unit': 'CUP'},
        {'name': 'eggs',            'quantity': '2',   'unit': ''},
        {'name': 'edamame',         'quantity': '100', 'unit': 'G',    'notes': 'shelled, frozen is fine'},
        {'name': 'tamari soy sauce','quantity': '3',   'unit': 'TBSP'},
        {'name': 'sesame oil',      'quantity': '1',   'unit': 'TBSP'},
        {'name': 'fresh ginger',    'quantity': '1',   'unit': 'TSP',  'notes': 'grated'},
        {'name': 'garlic',          'quantity': '2',   'unit': '',     'notes': 'cloves, minced'},
        {'name': 'spring onion',    'quantity': '2',   'unit': 'WHOLE','notes': 'sliced'},
        {'name': 'sesame seeds',    'quantity': '1',   'unit': 'TSP'},
    ],
)

create_recipe(
    author      = staff1,
    title       = "Greek Yogurt Protein Pancakes",
    description = "Fluffy high-protein pancakes ready in 15 minutes — perfect pre-workout fuel.",
    difficulty  = "EASY",
    prep        = 5,
    cook        = 10,
    servings    = 2,
    calories    = 390,
    dietary     = ['NO_NUTS', 'VEGETARIAN'],
    locked      = False,
    instructions = (
        "1. In a bowl, whisk together oats (blended to flour), baking powder, and a pinch of salt.\n"
        "2. In a separate bowl, mix Greek yogurt, eggs, and vanilla extract until smooth.\n"
        "3. Fold wet ingredients into dry ingredients until just combined — don't overmix.\n"
        "4. Heat a non-stick pan over medium heat and lightly grease with cooking spray.\n"
        "5. Pour roughly 1/4 cup batter per pancake. Cook until bubbles form on the surface (2–3 min), then flip.\n"
        "6. Cook 1–2 more minutes until golden. Serve topped with fresh berries and a drizzle of honey."
    ),
    ingredients = [
        {'name': 'rolled oats',      'quantity': '1',   'unit': 'CUP',  'notes': 'blended into flour'},
        {'name': 'Greek yogurt',     'quantity': '150', 'unit': 'G',    'notes': 'plain, full-fat'},
        {'name': 'eggs',             'quantity': '2',   'unit': ''},
        {'name': 'baking powder',    'quantity': '1',   'unit': 'TSP'},
        {'name': 'vanilla extract',  'quantity': '0.5', 'unit': 'TSP'},
        {'name': 'mixed berries',    'quantity': '80',  'unit': 'G'},
        {'name': 'honey',            'quantity': '1',   'unit': 'TBSP'},
    ],
)

create_recipe(
    author      = coach1,
    title       = "Spicy Tuna Rice Cake Stack",
    description = "A quick, no-cook high-protein snack or light lunch with zero prep drama.",
    difficulty  = "EASY",
    prep        = 8,
    cook        = 0,
    servings    = 1,
    calories    = 280,
    dietary     = ['NO_GLUTEN', 'NO_DAIRY_LACTOSE', 'NO_NUTS'],
    locked      = False,
    instructions = (
        "1. Drain canned tuna and place in a bowl.\n"
        "2. Mix tuna with sriracha, light mayo, soy sauce, and sesame oil.\n"
        "3. Finely slice spring onion and cucumber.\n"
        "4. Lay out rice cakes on a plate.\n"
        "5. Spoon tuna mixture onto each rice cake.\n"
        "6. Top with cucumber, spring onion, and a sprinkle of sesame seeds. Serve immediately."
    ),
    ingredients = [
        {'name': 'canned tuna',      'quantity': '1',   'unit': 'WHOLE', 'notes': '130g can, drained'},
        {'name': 'plain rice cakes', 'quantity': '4',   'unit': ''},
        {'name': 'sriracha',         'quantity': '1',   'unit': 'TSP'},
        {'name': 'light mayonnaise', 'quantity': '1',   'unit': 'TBSP'},
        {'name': 'soy sauce',        'quantity': '0.5', 'unit': 'TSP'},
        {'name': 'sesame oil',       'quantity': '0.5', 'unit': 'TSP'},
        {'name': 'spring onion',     'quantity': '1',   'unit': 'WHOLE', 'notes': 'thinly sliced'},
        {'name': 'cucumber',         'quantity': '0.25','unit': 'WHOLE', 'notes': 'thinly sliced'},
        {'name': 'sesame seeds',     'quantity': '0.5', 'unit': 'TSP'},
    ],
)

create_recipe(
    author      = staff2,
    title       = "Lentil & Vegetable Soup",
    description = "A hearty, filling plant-based soup that batch cooks perfectly for the week.",
    difficulty  = "EASY",
    prep        = 10,
    cook        = 30,
    servings    = 4,
    calories    = 290,
    dietary     = ['VEGAN', 'NO_GLUTEN', 'NO_DAIRY_LACTOSE', 'NO_NUTS', 'NO_SEAFOOD'],
    locked      = False,
    instructions = (
        "1. Heat olive oil in a large pot over medium heat. Add diced onion and cook for 5 minutes until soft.\n"
        "2. Add garlic, cumin, turmeric, and smoked paprika. Stir and cook for 1 minute until fragrant.\n"
        "3. Add diced carrots and celery. Cook for 3 minutes.\n"
        "4. Rinse red lentils and add to the pot along with vegetable broth and canned tomatoes.\n"
        "5. Bring to a boil, then reduce to a simmer for 20–25 minutes until lentils are completely soft.\n"
        "6. Season with salt and pepper. Stir in spinach and cook for 1 more minute.\n"
        "7. Serve with a squeeze of lemon juice. Keeps in the fridge for 5 days."
    ),
    ingredients = [
        {'name': 'red lentils',      'quantity': '200', 'unit': 'G',    'notes': 'rinsed'},
        {'name': 'onion',            'quantity': '1',   'unit': 'WHOLE','notes': 'diced'},
        {'name': 'garlic',           'quantity': '3',   'unit': '',     'notes': 'cloves, minced'},
        {'name': 'carrot',           'quantity': '2',   'unit': 'WHOLE','notes': 'diced'},
        {'name': 'celery',           'quantity': '2',   'unit': 'WHOLE','notes': 'stalks, sliced'},
        {'name': 'canned tomatoes',  'quantity': '400', 'unit': 'G',    'notes': '1 can'},
        {'name': 'vegetable broth',  'quantity': '1',   'unit': 'L'},
        {'name': 'baby spinach',     'quantity': '60',  'unit': 'G'},
        {'name': 'olive oil',        'quantity': '1',   'unit': 'TBSP'},
        {'name': 'cumin',            'quantity': '1',   'unit': 'TSP'},
        {'name': 'turmeric',         'quantity': '0.5', 'unit': 'TSP'},
        {'name': 'smoked paprika',   'quantity': '1',   'unit': 'TSP'},
        {'name': 'lemon juice',      'quantity': '1',   'unit': 'TBSP'},
    ],
)

create_recipe(
    author      = staff1,
    title       = "Egg White & Veggie Omelette",
    description = "A light, low-calorie breakfast packed with protein and micronutrients.",
    difficulty  = "EASY",
    prep        = 5,
    cook        = 8,
    servings    = 1,
    calories    = 210,
    dietary     = ['NO_GLUTEN', 'NO_DAIRY_LACTOSE', 'NO_NUTS', 'VEGETARIAN'],
    locked      = False,
    instructions = (
        "1. Whisk egg whites with a pinch of salt, pepper, and dried herbs.\n"
        "2. Dice capsicum, mushrooms, and spinach.\n"
        "3. Heat a non-stick pan over medium heat with cooking spray.\n"
        "4. Sauté vegetables for 2–3 minutes until slightly softened. Remove from pan.\n"
        "5. Pour egg whites into the pan. As the edges set, lift with a spatula and tilt the pan to let liquid egg flow underneath.\n"
        "6. When almost set, add vegetables to one half. Fold the omelette over and slide onto a plate.\n"
        "7. Season and serve immediately."
    ),
    ingredients = [
        {'name': 'egg whites',       'quantity': '5',   'unit': '',     'notes': 'approx 150ml'},
        {'name': 'red capsicum',     'quantity': '0.5', 'unit': 'WHOLE','notes': 'diced'},
        {'name': 'mushrooms',        'quantity': '60',  'unit': 'G',    'notes': 'sliced'},
        {'name': 'baby spinach',     'quantity': '30',  'unit': 'G'},
        {'name': 'dried mixed herbs','quantity': '0.5', 'unit': 'TSP'},
    ],
)

create_recipe(
    author      = coach3,
    title       = "Slow-Cooker Chicken & White Bean Stew",
    description = "Set it and forget it — a high-protein, gut-friendly stew ready when you get home.",
    difficulty  = "MEDIUM",
    prep        = 15,
    cook        = 360,
    servings    = 4,
    calories    = 440,
    dietary     = ['NO_GLUTEN', 'NO_DAIRY_LACTOSE', 'NO_NUTS'],
    locked      = True,
    instructions = (
        "1. Season chicken thighs with salt, pepper, smoked paprika, and garlic powder.\n"
        "2. Add chicken to the slow cooker. Scatter drained white beans around the chicken.\n"
        "3. Add diced onion, celery, carrot, canned tomatoes, and chicken broth.\n"
        "4. Add rosemary sprig and bay leaves. Stir gently.\n"
        "5. Cook on LOW for 6–8 hours or HIGH for 3–4 hours.\n"
        "6. Remove chicken and shred with two forks. Return to pot and stir.\n"
        "7. Stir in kale and let wilt for 5 minutes before serving."
    ),
    ingredients = [
        {'name': 'chicken thighs',   'quantity': '600', 'unit': 'G',    'notes': 'boneless, skinless'},
        {'name': 'white beans',      'quantity': '400', 'unit': 'G',    'notes': '1 can, drained'},
        {'name': 'onion',            'quantity': '1',   'unit': 'WHOLE','notes': 'diced'},
        {'name': 'carrot',           'quantity': '2',   'unit': 'WHOLE','notes': 'chopped'},
        {'name': 'celery',           'quantity': '2',   'unit': 'WHOLE','notes': 'stalks, chopped'},
        {'name': 'canned tomatoes',  'quantity': '400', 'unit': 'G',    'notes': '1 can'},
        {'name': 'chicken broth',    'quantity': '500', 'unit': 'ML'},
        {'name': 'kale',             'quantity': '80',  'unit': 'G',    'notes': 'roughly chopped'},
        {'name': 'rosemary',         'quantity': '1',   'unit': 'WHOLE','notes': 'fresh sprig'},
        {'name': 'bay leaves',       'quantity': '2',   'unit': ''},
        {'name': 'smoked paprika',   'quantity': '1',   'unit': 'TSP'},
        {'name': 'garlic powder',    'quantity': '1',   'unit': 'TSP'},
    ],
)

create_recipe(
    author      = staff2,
    title       = "Smoked Salmon & Avocado Protein Bowl",
    description = "A premium no-cook recovery bowl rich in omega-3s, healthy fats, and complete protein.",
    difficulty  = "EASY",
    prep        = 10,
    cook        = 0,
    servings    = 1,
    calories    = 520,
    dietary     = ['NO_GLUTEN', 'NO_DAIRY_LACTOSE', 'NO_NUTS'],
    locked      = True,
    instructions = (
        "1. Cook quinoa in advance and allow to cool (or use pre-cooked).\n"
        "2. Halve and slice the avocado. Squeeze lemon juice over it to prevent browning.\n"
        "3. Soft-boil the egg: bring water to a boil, lower the egg in gently, cook exactly 6.5 minutes, transfer to ice water, peel.\n"
        "4. Arrange quinoa in a bowl as a base.\n"
        "5. Place smoked salmon, sliced avocado, and halved soft-boiled egg on top.\n"
        "6. Add cucumber ribbons and capers.\n"
        "7. Drizzle with olive oil and lemon juice. Finish with cracked black pepper and fresh dill."
    ),
    ingredients = [
        {'name': 'smoked salmon',    'quantity': '100', 'unit': 'G'},
        {'name': 'avocado',          'quantity': '0.5', 'unit': 'WHOLE'},
        {'name': 'egg',              'quantity': '1',   'unit': ''},
        {'name': 'cooked quinoa',    'quantity': '0.5', 'unit': 'CUP'},
        {'name': 'cucumber',         'quantity': '0.25','unit': 'WHOLE', 'notes': 'peeled into ribbons'},
        {'name': 'capers',           'quantity': '1',   'unit': 'TBSP'},
        {'name': 'lemon juice',      'quantity': '1',   'unit': 'TBSP'},
        {'name': 'olive oil',        'quantity': '1',   'unit': 'TBSP'},
        {'name': 'fresh dill',       'quantity': '1',   'unit': 'PINCH'},
    ],
)

# ─────────────────────────────────────────────
# 7. Exercises
# ─────────────────────────────────────────────
print("\n── Creating Exercises ──")

def create_exercise(title, description, instructions, muscle_group, difficulty, goal, created_by):
    if Exercise.objects.filter(title=title).exists():
        print(f"  [skip] Exercise already exists: '{title}'")
        return Exercise.objects.get(title=title)
    ex = Exercise.objects.create(
        title=title,
        description=description,
        instructions=instructions,
        muscle_group=muscle_group,
        difficulty=difficulty,
        goal=goal,
        created_by=created_by,   # <-- FIX: assign a valid user
    )
    print(f"  [created] Exercise: '{title}'")
    return ex

# Use the first staff user as the creator for all exercises
exercise_creator = staff1   # staff1 is already defined earlier in the script

# ── CHEST ──
bench_press = create_exercise(
    title        = "Barbell Bench Press",
    description  = "The classic compound chest exercise for building upper body mass and strength.",
    instructions = (
        "1. Lie flat on the bench, feet firmly on the floor.\n"
        "2. Grip the bar slightly wider than shoulder-width, thumbs wrapped around.\n"
        "3. Unrack the bar and hold it directly above your chest with arms fully extended.\n"
        "4. Lower the bar slowly to your mid-chest, keeping elbows at roughly 45°.\n"
        "5. Press the bar back up explosively until arms are fully extended.\n"
        "6. Keep your shoulder blades retracted and back slightly arched throughout."
    ),
    muscle_group = "CHEST",
    difficulty   = "MEDIUM",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

incline_db_press = create_exercise(
    title        = "Incline Dumbbell Press",
    description  = "Targets the upper chest with a more natural pressing angle than the barbell version.",
    instructions = (
        "1. Set a bench to 30–45°. Sit back with a dumbbell in each hand resting on your thighs.\n"
        "2. Kick the dumbbells up as you lie back, positioning them at chest level.\n"
        "3. Press the dumbbells upward and slightly inward until your arms are extended.\n"
        "4. Lower slowly with control, feeling a stretch in the upper chest.\n"
        "5. Keep your feet flat, core tight, and avoid flaring elbows excessively."
    ),
    muscle_group = "CHEST",
    difficulty   = "MEDIUM",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

push_up = create_exercise(
    title        = "Push-Up",
    description  = "A foundational bodyweight exercise that trains the chest, triceps, and shoulders.",
    instructions = (
        "1. Start in a high plank position, hands just wider than shoulder-width.\n"
        "2. Keep your body in a straight line from head to heels — don't let your hips sag.\n"
        "3. Lower your chest toward the floor by bending your elbows to about 45°.\n"
        "4. Push through your palms to return to the starting position.\n"
        "5. Breathe in on the way down, out on the way up."
    ),
    muscle_group = "CHEST",
    difficulty   = "EASY",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

# ── BACK ──
pull_up = create_exercise(
    title        = "Pull-Up",
    description  = "One of the best exercises for building a wide, strong back using only bodyweight.",
    instructions = (
        "1. Hang from a pull-up bar with an overhand grip slightly wider than shoulder-width.\n"
        "2. Depress and retract your shoulder blades before initiating the pull.\n"
        "3. Pull your chest toward the bar, driving your elbows down and back.\n"
        "4. Pause briefly at the top when your chin clears the bar.\n"
        "5. Lower yourself with control until your arms are fully extended.\n"
        "6. Avoid swinging or kipping — keep the movement controlled."
    ),
    muscle_group = "BACK",
    difficulty   = "HARD",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

bent_over_row = create_exercise(
    title        = "Barbell Bent-Over Row",
    description  = "A compound pulling movement that builds thickness in the mid and upper back.",
    instructions = (
        "1. Stand with feet hip-width apart, grip the barbell with an overhand grip.\n"
        "2. Hinge at the hips until your torso is roughly parallel to the floor, knees slightly bent.\n"
        "3. Keep your back flat and core braced throughout the lift.\n"
        "4. Pull the bar toward your lower chest / upper abdomen, driving elbows back.\n"
        "5. Squeeze your shoulder blades together at the top.\n"
        "6. Lower the bar with control — don't let it crash down."
    ),
    muscle_group = "BACK",
    difficulty   = "MEDIUM",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

lat_pulldown = create_exercise(
    title        = "Lat Pulldown",
    description  = "A cable machine exercise that targets the latissimus dorsi for a wider back.",
    instructions = (
        "1. Sit at the lat pulldown machine and grip the bar wider than shoulder-width.\n"
        "2. Secure your thighs under the pad and sit tall with a slight arch in your lower back.\n"
        "3. Pull the bar down toward your upper chest, leading with your elbows.\n"
        "4. Squeeze your lats at the bottom of the movement.\n"
        "5. Return the bar slowly, fully extending your arms at the top.\n"
        "6. Avoid leaning back excessively — keep the torso relatively upright."
    ),
    muscle_group = "BACK",
    difficulty   = "EASY",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

# ── LEGS ──
barbell_squat = create_exercise(
    title        = "Barbell Back Squat",
    description  = "The king of lower body exercises — builds leg mass, strength, and overall athleticism.",
    instructions = (
        "1. Set the barbell at upper-chest height on the rack. Step under it so the bar rests on your upper traps.\n"
        "2. Grip the bar just outside your shoulders and unrack it, stepping back with feet shoulder-width apart.\n"
        "3. Brace your core, take a deep breath, and push your knees out as you squat down.\n"
        "4. Descend until your thighs are at least parallel to the floor.\n"
        "5. Drive through your heels to stand back up, keeping your chest up throughout.\n"
        "6. Lock out at the top, exhale, then reset for the next rep."
    ),
    muscle_group = "LEGS",
    difficulty   = "HARD",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

romanian_deadlift = create_exercise(
    title        = "Romanian Deadlift",
    description  = "A hip-hinge movement that targets the hamstrings and glutes with excellent stretch.",
    instructions = (
        "1. Stand with feet hip-width apart, holding a barbell or dumbbells in front of your thighs.\n"
        "2. Keep a slight bend in your knees — this stays fixed throughout the lift.\n"
        "3. Hinge at the hips, pushing them backward as you lower the weight down your legs.\n"
        "4. Lower until you feel a deep stretch in your hamstrings (typically just below the knee).\n"
        "5. Drive your hips forward to return to standing, squeezing your glutes at the top.\n"
        "6. Keep the bar close to your legs and your back flat at all times."
    ),
    muscle_group = "LEGS",
    difficulty   = "MEDIUM",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

walking_lunge = create_exercise(
    title        = "Walking Lunge",
    description  = "A dynamic unilateral exercise that builds leg strength, balance, and coordination.",
    instructions = (
        "1. Stand tall with feet together, hands on hips or holding dumbbells at your sides.\n"
        "2. Step forward with your right foot and lower your left knee toward the floor.\n"
        "3. Your front knee should be directly above your ankle — don't let it cave inward.\n"
        "4. Push through your front heel to bring your back foot forward and into the next step.\n"
        "5. Alternate legs continuously as you walk forward.\n"
        "6. Keep your torso upright and core engaged throughout."
    ),
    muscle_group = "LEGS",
    difficulty   = "EASY",
    goal         = "WEIGHT_LOSS",
    created_by   = exercise_creator,
)

leg_press = create_exercise(
    title        = "Leg Press",
    description  = "A machine-based compound exercise for loading the quads, hamstrings, and glutes safely.",
    instructions = (
        "1. Sit in the leg press machine with your back flat against the pad.\n"
        "2. Place feet shoulder-width apart on the platform, toes slightly turned out.\n"
        "3. Release the safety handles and lower the platform by bending your knees to 90°.\n"
        "4. Press through your heels to extend your legs, stopping just short of locking out.\n"
        "5. Control the descent — don't let the weight crash down.\n"
        "6. Never let your lower back peel off the seat."
    ),
    muscle_group = "LEGS",
    difficulty   = "EASY",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

# ── SHOULDERS ──
overhead_press = create_exercise(
    title        = "Barbell Overhead Press",
    description  = "The primary compound movement for building strong, broad shoulders.",
    instructions = (
        "1. Set the barbell at collar-bone height in a rack. Grip just outside shoulder-width.\n"
        "2. Unrack the bar, holding it at the top of your chest with elbows forward.\n"
        "3. Brace your core and press the bar directly overhead, slightly back once it clears your head.\n"
        "4. Fully extend your arms at the top, shrugging your traps to lock out.\n"
        "5. Lower the bar back to the starting position under control.\n"
        "6. Keep your glutes squeezed and avoid excessive lower-back arch."
    ),
    muscle_group = "SHOULDERS",
    difficulty   = "MEDIUM",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

lateral_raise = create_exercise(
    title        = "Dumbbell Lateral Raise",
    description  = "An isolation exercise targeting the lateral deltoid for wider-looking shoulders.",
    instructions = (
        "1. Stand with feet shoulder-width apart, a light dumbbell in each hand at your sides.\n"
        "2. With a slight bend in your elbows, raise your arms out to the sides until parallel to the floor.\n"
        "3. Lead with your elbows, not your wrists — think of pouring water from a jug.\n"
        "4. Pause briefly at the top with shoulders packed down.\n"
        "5. Lower the dumbbells slowly under control — the eccentric is where the work happens.\n"
        "6. Avoid swinging — use lighter weight and full control."
    ),
    muscle_group = "SHOULDERS",
    difficulty   = "EASY",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

face_pull = create_exercise(
    title        = "Cable Face Pull",
    description  = "A rear-delt and rotator cuff exercise that improves shoulder health and posture.",
    instructions = (
        "1. Set a cable pulley to head height with a rope attachment.\n"
        "2. Grip both ends of the rope with an overhand grip, step back to create tension.\n"
        "3. Pull the rope toward your face, flaring your elbows out to the sides.\n"
        "4. Externally rotate your shoulders so your hands end up beside your ears.\n"
        "5. Squeeze your rear delts and hold for a second at full contraction.\n"
        "6. Return slowly to the start. Keep your torso upright — don't lean back."
    ),
    muscle_group = "SHOULDERS",
    difficulty   = "EASY",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

# ── ARMS ──
barbell_curl = create_exercise(
    title        = "Barbell Bicep Curl",
    description  = "The fundamental bicep exercise for building arm size and strength.",
    instructions = (
        "1. Stand with feet hip-width apart, gripping a barbell with an underhand grip at hip level.\n"
        "2. Keep your elbows pinned to your sides throughout the movement.\n"
        "3. Curl the bar upward by flexing your elbows, bringing the bar toward your shoulders.\n"
        "4. Squeeze your biceps hard at the top.\n"
        "5. Lower the bar slowly under full control — don't just drop it.\n"
        "6. Avoid swinging your body to generate momentum."
    ),
    muscle_group = "ARMS",
    difficulty   = "EASY",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

tricep_dip = create_exercise(
    title        = "Tricep Dip",
    description  = "A bodyweight compound movement that builds the triceps and lower chest.",
    instructions = (
        "1. Grip parallel dip bars with arms extended, body hanging freely.\n"
        "2. Lean slightly forward (about 15–20°) to emphasise the triceps.\n"
        "3. Lower yourself by bending your elbows until your upper arms are parallel to the floor.\n"
        "4. Press back up through your palms until your arms are fully extended.\n"
        "5. Keep your elbows from flaring too wide — point them slightly back.\n"
        "6. Add weight with a dip belt once bodyweight becomes easy."
    ),
    muscle_group = "ARMS",
    difficulty   = "MEDIUM",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

hammer_curl = create_exercise(
    title        = "Hammer Curl",
    description  = "A neutral-grip curl that targets the brachialis and brachioradialis for thicker arms.",
    instructions = (
        "1. Stand holding dumbbells at your sides with a neutral grip (palms facing each other).\n"
        "2. Keeping your elbows tucked, curl one or both dumbbells toward your shoulders.\n"
        "3. Don't rotate your wrist — keep the neutral grip throughout.\n"
        "4. Squeeze at the top, then lower with control.\n"
        "5. Alternate arms or do both together — either works."
    ),
    muscle_group = "ARMS",
    difficulty   = "EASY",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

# ── CORE ──
plank = create_exercise(
    title        = "Plank",
    description  = "The foundational isometric core exercise for building stability and endurance.",
    instructions = (
        "1. Get into a forearm plank position — elbows directly under your shoulders.\n"
        "2. Form a straight line from head to heels — no sagging hips or raised glutes.\n"
        "3. Squeeze your abs, glutes, and quads simultaneously.\n"
        "4. Breathe steadily — don't hold your breath.\n"
        "5. Hold for the prescribed time. Build from 20 seconds up to 60+ seconds progressively."
    ),
    muscle_group = "CORE",
    difficulty   = "EASY",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

cable_crunch = create_exercise(
    title        = "Cable Crunch",
    description  = "A weighted core exercise that allows progressive overload on the abdominals.",
    instructions = (
        "1. Attach a rope to a high cable pulley. Kneel facing the machine.\n"
        "2. Hold the rope beside your head, elbows pointing down.\n"
        "3. Crunch downward, bringing your elbows toward your knees by flexing your spine.\n"
        "4. Focus on rounding your lower back — don't just hinge at the hips.\n"
        "5. Hold the contraction for a second, then return to upright slowly.\n"
        "6. The weight should make 10–15 reps challenging."
    ),
    muscle_group = "CORE",
    difficulty   = "MEDIUM",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

hanging_leg_raise = create_exercise(
    title        = "Hanging Leg Raise",
    description  = "An advanced core exercise that targets the lower abs and hip flexors.",
    instructions = (
        "1. Hang from a pull-up bar with a shoulder-width overhand grip.\n"
        "2. Keep your legs together and start with them hanging straight down.\n"
        "3. Raise your legs by flexing at the hips and curling your pelvis upward.\n"
        "4. Aim to bring your legs to 90° or higher — the higher the better for lower abs.\n"
        "5. Lower your legs slowly — don't swing them down.\n"
        "6. Bend your knees slightly if the straight-leg version is too difficult at first."
    ),
    muscle_group = "CORE",
    difficulty   = "HARD",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

# ── FULL BODY / CARDIO ──
deadlift = create_exercise(
    title        = "Conventional Deadlift",
    description  = "The ultimate full-body strength exercise — works nearly every muscle in the body.",
    instructions = (
        "1. Stand with feet hip-width apart, bar over mid-foot. Grip just outside your legs.\n"
        "2. Hinge down, keeping your chest up, back flat, and hips above your knees.\n"
        "3. Take a deep breath into your belly and brace your core hard before lifting.\n"
        "4. Push the floor away with your legs while simultaneously pulling the bar into your body.\n"
        "5. Lock out at the top by extending your hips, squeezing your glutes.\n"
        "6. Hinge back down with control — don't round your lower back on the descent."
    ),
    muscle_group = "FULL_BODY",
    difficulty   = "HARD",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

burpee = create_exercise(
    title        = "Burpee",
    description  = "A high-intensity full-body exercise that spikes heart rate and burns calories fast.",
    instructions = (
        "1. Stand with feet shoulder-width apart.\n"
        "2. Drop your hands to the floor and jump your feet back into a push-up position.\n"
        "3. Perform one push-up (optional but recommended).\n"
        "4. Jump your feet back toward your hands.\n"
        "5. Explode upward into a jump, reaching your arms overhead.\n"
        "6. Land softly and immediately begin the next rep."
    ),
    muscle_group = "FULL_BODY",
    difficulty   = "HARD",
    goal         = "WEIGHT_LOSS",
    created_by   = exercise_creator,
)

kettlebell_swing = create_exercise(
    title        = "Kettlebell Swing",
    description  = "A ballistic hip-hinge exercise that builds power, burns fat, and conditions the posterior chain.",
    instructions = (
        "1. Stand with feet shoulder-width apart, kettlebell on the floor slightly in front of you.\n"
        "2. Hinge at the hips and grip the kettlebell with both hands.\n"
        "3. Hike the kettlebell back between your legs, keeping a flat back.\n"
        "4. Drive your hips forward explosively, letting the kettlebell float up to chest height.\n"
        "5. Let it swing back between your legs — absorb it with your hips, not your back.\n"
        "6. This is a hip hinge, not a squat — your hips drive the movement, not your arms."
    ),
    muscle_group = "FULL_BODY",
    difficulty   = "MEDIUM",
    goal         = "CARDIO",
    created_by   = exercise_creator,
)

box_jump = create_exercise(
    title        = "Box Jump",
    description  = "A plyometric exercise that develops explosive leg power and cardiovascular fitness.",
    instructions = (
        "1. Stand facing a sturdy box, feet shoulder-width apart.\n"
        "2. Dip into a quarter squat, swinging your arms back.\n"
        "3. Explode upward, driving your arms forward and jumping onto the box.\n"
        "4. Land softly with both feet flat on the box, knees slightly bent to absorb impact.\n"
        "5. Stand tall on the box, then step (don't jump) back down one foot at a time.\n"
        "6. Start with a lower box and progress height gradually."
    ),
    muscle_group = "LEGS",
    difficulty   = "MEDIUM",
    goal         = "CARDIO",
    created_by   = exercise_creator,
)

mountain_climber = create_exercise(
    title        = "Mountain Climber",
    description  = "A dynamic core and cardio exercise that works the abs, shoulders, and hip flexors.",
    instructions = (
        "1. Start in a high plank position, wrists under shoulders, body in a straight line.\n"
        "2. Drive your right knee toward your chest, then quickly switch — bringing the left knee in as the right goes back.\n"
        "3. Alternate legs rapidly in a running motion while keeping your hips level.\n"
        "4. Keep your core tight and don't let your hips rise or sag.\n"
        "5. Breathe continuously — don't hold your breath.\n"
        "6. Slow the tempo down if you need to maintain form."
    ),
    muscle_group = "CORE",
    difficulty   = "MEDIUM",
    goal         = "CARDIO",
    created_by   = exercise_creator,
)

# ── SHOULDERS (additional) ──
overhead_arnold_press = create_exercise(
    title        = "Arnold Press",
    description  = "A dumbbell shoulder press variation that hits all three deltoid heads through rotation.",
    instructions = (
        "1. Sit on an upright bench holding two dumbbells at shoulder height, palms facing you.\n"
        "2. As you press the dumbbells upward, rotate your wrists outward so your palms face away at the top.\n"
        "3. Fully extend your arms overhead — don't lock out aggressively.\n"
        "4. Reverse the rotation on the way down, returning to the starting position with palms facing you.\n"
        "5. Keep your core braced and avoid leaning back.\n"
        "6. Control the descent — don't drop the weights."
    ),
    muscle_group = "SHOULDERS",
    difficulty   = "MEDIUM",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

cable_lateral_raise = create_exercise(
    title        = "Cable Lateral Raise",
    description  = "A cable variation of the lateral raise that maintains constant tension on the side deltoid.",
    instructions = (
        "1. Stand sideways to a low cable pulley, handle in the far hand, arm across your body.\n"
        "2. Keep a slight bend in your elbow throughout the movement.\n"
        "3. Raise your arm out to the side until it's roughly parallel to the floor.\n"
        "4. Lead with your elbow, not your wrist — think about lifting your elbow up and out.\n"
        "5. Lower slowly under control — resist the cable pull on the way down.\n"
        "6. Complete all reps on one side before switching."
    ),
    muscle_group = "SHOULDERS",
    difficulty   = "EASY",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

# ── ARMS (additional) ──
close_grip_bench = create_exercise(
    title        = "Close-Grip Bench Press",
    description  = "A barbell pressing variation that shifts the emphasis to the triceps.",
    instructions = (
        "1. Lie flat on a bench and grip the barbell with hands shoulder-width apart or slightly narrower.\n"
        "2. Unrack the bar and hold it above your lower chest.\n"
        "3. Lower the bar to your lower chest/upper abdomen, keeping your elbows tucked close to your sides.\n"
        "4. Press back up to full extension, focusing on squeezing the triceps.\n"
        "5. Keep your wrists straight — don't let them bend back under load.\n"
        "6. Avoid gripping too narrow as this strains the wrists."
    ),
    muscle_group = "ARMS",
    difficulty   = "MEDIUM",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

preacher_curl = create_exercise(
    title        = "Preacher Curl",
    description  = "An isolation curl performed on a preacher bench that eliminates cheating and targets the bicep peak.",
    instructions = (
        "1. Sit at the preacher bench and rest your upper arms on the angled pad, armpits at the top edge.\n"
        "2. Grip the barbell or EZ-bar with a supinated (underhand) grip.\n"
        "3. Curl the weight upward until your forearms are nearly vertical, squeezing the biceps hard.\n"
        "4. Lower slowly until your arms are almost fully extended — don't lock out completely.\n"
        "5. Avoid letting the weight drop quickly — the eccentric (lowering) phase is where growth happens.\n"
        "6. Keep your upper arms pressed firmly into the pad throughout."
    ),
    muscle_group = "ARMS",
    difficulty   = "EASY",
    goal         = "MUSCLE_GAIN",
    created_by   = exercise_creator,
)

# ── CORE (additional) ──
ab_wheel_rollout = create_exercise(
    title        = "Ab Wheel Rollout",
    description  = "One of the most effective core exercises, training anti-extension strength of the entire trunk.",
    instructions = (
        "1. Kneel on a mat and grip the ab wheel handles with both hands directly below your shoulders.\n"
        "2. Brace your core hard — your lower back must not arch during the movement.\n"
        "3. Slowly roll the wheel forward, extending your body toward the floor.\n"
        "4. Roll out as far as you can while maintaining a neutral spine — stop before your hips sag.\n"
        "5. Contract your core and pull the wheel back to the starting position.\n"
        "6. Beginners: limit the range of motion. Advanced: aim to reach full extension."
    ),
    muscle_group = "CORE",
    difficulty   = "HARD",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

dead_bug = create_exercise(
    title        = "Dead Bug",
    description  = "A beginner-friendly core stability exercise that trains deep abdominal control and coordination.",
    instructions = (
        "1. Lie on your back with your arms extended straight above your chest and knees bent at 90° in the air (tabletop position).\n"
        "2. Press your lower back firmly into the floor — maintain this contact throughout.\n"
        "3. Slowly lower your right arm overhead and your left leg toward the floor simultaneously.\n"
        "4. Lower as far as you can without your lower back lifting off the floor.\n"
        "5. Return to the starting position and repeat on the opposite side.\n"
        "6. Move slowly and with control — this is about stability, not speed."
    ),
    muscle_group = "CORE",
    difficulty   = "EASY",
    goal         = "FLEXIBILITY",
    created_by   = exercise_creator,
)

# ── FULL BODY (additional) ──
turkish_get_up = create_exercise(
    title        = "Turkish Get-Up",
    description  = "A complex full-body movement that builds shoulder stability, core strength, and mobility simultaneously.",
    instructions = (
        "1. Lie on your back, holding a kettlebell in your right hand, arm extended toward the ceiling.\n"
        "2. Bend your right knee, foot flat on the floor. Keep your eyes on the kettlebell at all times.\n"
        "3. Roll onto your left elbow, then press up to your left hand.\n"
        "4. Lift your hips off the floor into a bridge position.\n"
        "5. Sweep your left leg back into a kneeling position.\n"
        "6. Stand up tall, then reverse each step back to the floor.\n"
        "7. Complete all reps on one side before switching. Start with no weight to learn the pattern."
    ),
    muscle_group = "FULL_BODY",
    difficulty   = "HARD",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

farmers_carry = create_exercise(
    title        = "Farmer's Carry",
    description  = "A loaded carry exercise that builds grip strength, core stability, and total body conditioning.",
    instructions = (
        "1. Stand between two heavy dumbbells or kettlebells.\n"
        "2. Hinge down and pick them up with a neutral grip, keeping your back flat.\n"
        "3. Stand tall — shoulders packed back and down, core braced, chin neutral.\n"
        "4. Walk forward with controlled steps for the prescribed distance or time.\n"
        "5. Keep your breathing steady and your torso upright — don't lean to either side.\n"
        "6. Set the weights down with control at the end of each rep."
    ),
    muscle_group = "FULL_BODY",
    difficulty   = "MEDIUM",
    goal         = "STRENGTH",
    created_by   = exercise_creator,
)

# ─────────────────────────────────────────────
# 8. Workout Plans
# ─────────────────────────────────────────────
print("\n── Creating Workout Plans ──")

def create_workout(author, title, description, body, difficulty, duration_minutes, goal, locked, exercises_list):
    if WorkoutPlan.objects.filter(title=title).exists():
        print(f"  [skip] WorkoutPlan already exists: '{title}'")
        return WorkoutPlan.objects.get(title=title)

    plan = WorkoutPlan.objects.create(
        author=author,
        title=title,
        description=description,
        body=body,
        difficulty=difficulty,
        duration_minutes=duration_minutes,
        goal=goal,
        locked=locked,
    )

    for i, ex_data in enumerate(exercises_list):
        WorkoutPlanExercise.objects.create(
            workout=plan,
            exercise=ex_data['exercise'],
            sets=ex_data['sets'],
            reps=ex_data['reps'],
            rest_seconds=ex_data.get('rest_seconds', 60),
            order=i + 1,
            notes=ex_data.get('notes', ''),
        )

    status = "🔒 locked" if locked else "🔓 unlocked"
    print(f"  [created] WorkoutPlan ({status}): '{title}' with {len(exercises_list)} exercises")
    return plan


create_workout(
    author           = staff1,
    title            = "Beginner Full Body Starter",
    description      = "A 3-day-a-week full body routine for complete beginners to build a foundation.",
    body             = (
        "This plan is designed for people who are new to resistance training. "
        "Each session hits all major muscle groups with simple, effective movements. "
        "Rest 60–90 seconds between sets and focus on learning proper form before adding weight. "
        "Perform this workout 3 times per week with at least one rest day between sessions."
    ),
    difficulty       = "EASY",
    duration_minutes = 45,
    goal             = "STRENGTH",
    locked           = False,
    exercises_list   = [
        {'exercise': push_up,          'sets': 3, 'reps': '10',    'rest_seconds': 60},
        {'exercise': barbell_squat,    'sets': 3, 'reps': '10',    'rest_seconds': 90},
        {'exercise': lat_pulldown,     'sets': 3, 'reps': '10',    'rest_seconds': 60},
        {'exercise': plank,            'sets': 3, 'reps': '30s',   'rest_seconds': 45},
        {'exercise': walking_lunge,    'sets': 2, 'reps': '12',    'rest_seconds': 60},
    ],
)

create_workout(
    author           = staff1,
    title            = "Intermediate Push Day",
    description      = "A chest, shoulder, and tricep focused session for those on a push/pull/legs split.",
    body             = (
        "Push day focuses on all pressing muscles — chest, anterior delts, and triceps. "
        "Start with the heavy compound movements when you're freshest, then move to isolation work. "
        "Rest 90–120 seconds on the main lifts and 60 seconds on isolation exercises. "
        "Aim to progressively add weight or reps each week."
    ),
    difficulty       = "MEDIUM",
    duration_minutes = 60,
    goal             = "MUSCLE_GAIN",
    locked           = False,
    exercises_list   = [
        {'exercise': bench_press,      'sets': 4, 'reps': '6-8',   'rest_seconds': 120, 'notes': 'Main lift — push for progressive overload'},
        {'exercise': incline_db_press, 'sets': 3, 'reps': '10-12', 'rest_seconds': 90},
        {'exercise': overhead_press,   'sets': 3, 'reps': '8-10',  'rest_seconds': 90},
        {'exercise': lateral_raise,    'sets': 3, 'reps': '15',    'rest_seconds': 60},
        {'exercise': tricep_dip,       'sets': 3, 'reps': '10-12', 'rest_seconds': 60},
        {'exercise': face_pull,        'sets': 2, 'reps': '15',    'rest_seconds': 45,  'notes': "Shoulder health — don't skip this"},
    ],
)

create_workout(
    author           = staff2,
    title            = "Intermediate Pull Day",
    description      = "A back and bicep session designed to build width, thickness, and arm size.",
    body             = (
        "Pull day targets all the major pulling muscles — lats, rhomboids, traps, rear delts, and biceps. "
        "Focus on driving your elbows, not your hands, on every pulling movement. "
        "The mind-muscle connection is especially important here. "
        "Pair with Push Day and Leg Day for a complete PPL split."
    ),
    difficulty       = "MEDIUM",
    duration_minutes = 55,
    goal             = "MUSCLE_GAIN",
    locked           = False,
    exercises_list   = [
        {'exercise': pull_up,          'sets': 4, 'reps': '6-8',   'rest_seconds': 120, 'notes': 'Add weight if bodyweight is easy'},
        {'exercise': bent_over_row,    'sets': 4, 'reps': '8-10',  'rest_seconds': 90},
        {'exercise': lat_pulldown,     'sets': 3, 'reps': '10-12', 'rest_seconds': 75},
        {'exercise': face_pull,        'sets': 3, 'reps': '15',    'rest_seconds': 60},
        {'exercise': barbell_curl,     'sets': 3, 'reps': '10-12', 'rest_seconds': 60},
        {'exercise': hammer_curl,      'sets': 3, 'reps': '12',    'rest_seconds': 45},
    ],
)

create_workout(
    author           = staff2,
    title            = "Leg Day — Strength Focus",
    description      = "A heavy lower body session built around the squat and deadlift for maximum strength.",
    body             = (
        "This leg day prioritises strength in the squat and deadlift pattern. "
        "The session starts with the most demanding exercises and finishes with accessory work. "
        "Rest 2–3 minutes between your heavy sets — don't rush it. "
        "Aim to add weight to the bar every 1–2 weeks."
    ),
    difficulty       = "HARD",
    duration_minutes = 75,
    goal             = "STRENGTH",
    locked           = False,
    exercises_list   = [
        {'exercise': barbell_squat,     'sets': 5, 'reps': '5',     'rest_seconds': 180, 'notes': 'Work up to a heavy top set'},
        {'exercise': romanian_deadlift, 'sets': 4, 'reps': '8',     'rest_seconds': 120},
        {'exercise': leg_press,         'sets': 3, 'reps': '10-12', 'rest_seconds': 90},
        {'exercise': walking_lunge,     'sets': 3, 'reps': '12',    'rest_seconds': 75,  'notes': '12 reps each leg'},
        {'exercise': hanging_leg_raise, 'sets': 3, 'reps': '12',    'rest_seconds': 60},
    ],
)

create_workout(
    author           = coach2,
    title            = "Fat Burn HIIT Circuit",
    description      = "A high-intensity circuit designed to maximise calorie burn and cardiovascular fitness.",
    body             = (
        "This HIIT circuit uses full-body movements to keep your heart rate elevated throughout. "
        "Perform each exercise back-to-back with minimal rest, then take a 90-second break between rounds. "
        "Complete 3–5 rounds depending on your fitness level. "
        "This style of training keeps your metabolism elevated for hours after the session."
    ),
    difficulty       = "HARD",
    duration_minutes = 30,
    goal             = "WEIGHT_LOSS",
    locked           = False,
    exercises_list   = [
        {'exercise': burpee,           'sets': 4, 'reps': '10',    'rest_seconds': 20,  'notes': 'Minimal rest — keep moving'},
        {'exercise': mountain_climber, 'sets': 4, 'reps': '30s',   'rest_seconds': 15},
        {'exercise': box_jump,         'sets': 4, 'reps': '8',     'rest_seconds': 30},
        {'exercise': kettlebell_swing, 'sets': 4, 'reps': '15',    'rest_seconds': 30},
        {'exercise': walking_lunge,    'sets': 3, 'reps': '20',    'rest_seconds': 20,  'notes': '20 total steps'},
    ],
)

create_workout(
    author           = coach3,
    title            = "Cardio & Core Conditioning",
    description      = "A moderate-intensity session combining cardiovascular work with core strengthening.",
    body             = (
        "This workout pairs cardio movements with core exercises in a steady-state format. "
        "It's ideal for active recovery days or as a complement to heavier strength sessions. "
        "Focus on breathing and maintaining good form throughout — this isn't a race. "
        "The core exercises are performed with control, not speed."
    ),
    difficulty       = "MEDIUM",
    duration_minutes = 40,
    goal             = "CARDIO",
    locked           = False,
    exercises_list   = [
        {'exercise': kettlebell_swing, 'sets': 3, 'reps': '20',    'rest_seconds': 60},
        {'exercise': mountain_climber, 'sets': 3, 'reps': '40s',   'rest_seconds': 45},
        {'exercise': plank,            'sets': 4, 'reps': '45s',   'rest_seconds': 30},
        {'exercise': cable_crunch,     'sets': 3, 'reps': '15',    'rest_seconds': 45},
        {'exercise': hanging_leg_raise,'sets': 3, 'reps': '10',    'rest_seconds': 60},
        {'exercise': burpee,           'sets': 3, 'reps': '8',     'rest_seconds': 60},
    ],
)

create_workout(
    author           = staff1,
    title            = "Advanced Powerlifting Program",
    description      = "An elite strength program built around the competition lifts for experienced athletes.",
    body             = (
        "This program is for experienced lifters with a solid base of strength. "
        "The three main lifts — squat, bench, and deadlift — are trained with heavy loads at low rep ranges. "
        "Accessory work targets weak points and prevents injury. "
        "Rest fully between heavy sets — strength training is not a race. "
        "This plan requires access to a barbell, rack, and bench."
    ),
    difficulty       = "HARD",
    duration_minutes = 90,
    goal             = "STRENGTH",
    locked           = True,
    exercises_list   = [
        {'exercise': barbell_squat,     'sets': 5, 'reps': '3',     'rest_seconds': 240, 'notes': 'Heavy — 85–90% of 1RM'},
        {'exercise': bench_press,       'sets': 5, 'reps': '3',     'rest_seconds': 240, 'notes': 'Heavy — 85–90% of 1RM'},
        {'exercise': deadlift,          'sets': 3, 'reps': '3',     'rest_seconds': 300, 'notes': 'Max effort sets'},
        {'exercise': overhead_press,    'sets': 4, 'reps': '5',     'rest_seconds': 180},
        {'exercise': bent_over_row,     'sets': 4, 'reps': '5',     'rest_seconds': 180},
        {'exercise': cable_crunch,      'sets': 3, 'reps': '15',    'rest_seconds': 60,  'notes': 'Core bracing for heavy lifts'},
    ],
)

create_workout(
    author           = staff2,
    title            = "Muscle Gain Hypertrophy Split",
    description      = "A premium upper/lower hypertrophy program optimised for maximum muscle growth.",
    body             = (
        "This program applies hypertrophy-specific training principles: moderate weight, higher volume, "
        "and short rest periods to maximise metabolic stress and muscle damage. "
        "Each exercise should be taken close to failure — leave 1–2 reps in reserve. "
        "Nutrition is critical: ensure you're in a caloric surplus with adequate protein (1.6–2.2g per kg). "
        "Train 4 days per week — Upper A / Lower A / Rest / Upper B / Lower B."
    ),
    difficulty       = "HARD",
    duration_minutes = 70,
    goal             = "MUSCLE_GAIN",
    locked           = True,
    exercises_list   = [
        {'exercise': incline_db_press,  'sets': 4, 'reps': '10-12', 'rest_seconds': 75,  'notes': 'Upper A — upper chest focus'},
        {'exercise': bent_over_row,     'sets': 4, 'reps': '10-12', 'rest_seconds': 75},
        {'exercise': overhead_press,    'sets': 3, 'reps': '12-15', 'rest_seconds': 60},
        {'exercise': lat_pulldown,      'sets': 3, 'reps': '12-15', 'rest_seconds': 60},
        {'exercise': lateral_raise,     'sets': 4, 'reps': '15-20', 'rest_seconds': 45},
        {'exercise': barbell_curl,      'sets': 3, 'reps': '12-15', 'rest_seconds': 45},
        {'exercise': tricep_dip,        'sets': 3, 'reps': '12-15', 'rest_seconds': 45},
        {'exercise': cable_crunch,      'sets': 3, 'reps': '15',    'rest_seconds': 45},
    ],
)

# ─────────────────────────────────────────────
# 9. Equipment
# ─────────────────────────────────────────────
print("\n── Creating Equipment ──")

def create_equipment(name, description, quantity):
    if EquipmentList.objects.filter(name=name).exists():
        print(f"  [skip] Equipment already exists: '{name}'")
        return
    EquipmentList.objects.create(name=name, description=description, quantity=quantity)
    print(f"  [created] Equipment: '{name}' x{quantity}")

create_equipment("Barbell",          "Olympic 20kg barbell for compound lifts.",                      8)
create_equipment("Dumbbells",        "Adjustable dumbbell rack ranging from 2.5kg to 50kg.",         20)
create_equipment("Squat Rack",       "Full power rack with safety bars and pull-up attachment.",      4)
create_equipment("Bench Press",      "Flat bench press station with barbell and weight plates.",      4)
create_equipment("Cable Machine",    "Dual-pulley cable station for rows, pulldowns, and curls.",     3)
create_equipment("Treadmill",        "Motorised treadmill with incline and heart rate monitor.",      6)
create_equipment("Rowing Machine",   "Air-resistance rowing ergometer for full-body cardio.",         4)
create_equipment("Kettlebells",      "Cast-iron kettlebell set from 8kg to 32kg.",                   16)
create_equipment("Leg Press",        "Plate-loaded 45-degree leg press machine.",                     2)
create_equipment("Pull-Up Station",  "Wall-mounted pull-up and dip station with multiple grips.",     3)


# ─────────────────────────────────────────────
# 10. Fitness Challenges
# ─────────────────────────────────────────────
print("\n── Creating Challenges ──")

Challenge.objects.get_or_create(
    title="7-Day Push-Up Challenge",
    description="Complete 50 push-ups daily for 7 days.",
    goal_target=7,
    start_date=timezone.make_aware(datetime(2026, 4, 1)),
    end_date=timezone.make_aware(datetime(2026, 4, 7)),
    created_by=staff1,
)

Challenge.objects.get_or_create(
    title="10K Steps Daily",
    description="Walk 10,000 steps every day for 14 days.",
    goal_target=14,
    start_date=timezone.make_aware(datetime(2026, 4, 1)),
    end_date=timezone.make_aware(datetime(2026, 4, 14)),
    created_by=staff2,
)

# ─────────────────────────────────────────────
# 11. Gym Schedule
# ─────────────────────────────────────────────
print("\n── Creating Gym Schedule ──")


gym_schedule_data = [
    # (GymInfo.day, open_time, close_time, is_open, is_open_24h),
    (GymInfo.MONDAY, None, None, True, True),
    (GymInfo.TUESDAY, None, None, True, True),
    (GymInfo.WEDNESDAY, None, None, True, True),
    (GymInfo.THURSDAY, None, None, True, True),
    (GymInfo.FRIDAY, None, None, True, True),
    (GymInfo.SATURDAY, time(6, 0), time(18, 0), True, False),
    (GymInfo.SUNDAY, time(6, 0), time(18, 0), True, False),
]

for day, open_time, close_time, is_open, is_open_24h in gym_schedule_data:
    obj, created = GymInfo.objects.get_or_create(day=day)
    if created:
        obj.open_time    = open_time
        obj.close_time   = close_time
        obj.is_open      = is_open
        obj.is_open_24h  = is_open_24h
        obj.save()
        print(f"  [created] {obj}")
    else:
        print(f"  [skip] GymInfo already exists: {obj}")

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("\n" + "="*50)
print("✅ Seed complete! Summary:")
print(f"   Users         : {User.objects.count()} total")
print(f"   Articles      : {Article.objects.count()} total")
print(f"   Recipes       : {Recipe.objects.count()} total")
print(f"   Exercises     : {Exercise.objects.count()} total")
print(f"   Workout Plans : {WorkoutPlan.objects.count()} total")
print(f"   Equipment     : {EquipmentList.objects.count()} total")
print(f"   Challenges    : {Challenge.objects.count()} total")
print(f"   Gym Schedule  : {GymInfo.objects.count()} days configured")
print()
print("Login credentials:")
print("  Admin  : admin@cufitness.com   / Admin@1234")
print("  Staff  : staff1@cufitness.com  / Staff@1234")
print("           staff2@cufitness.com  / Staff@1234")
print("  Members: member1@cufitness.com / Member@1234")
print("           member2@cufitness.com / Member@1234")
print("           member3@cufitness.com / Member@1234")
print("  Coach  : coach1@cufitness.com  / Coach@1234")
print("           coach2@cufitness.com  / Coach@1234")
print("           coach3@cufitness.com  / Coach@1234")
print("="*50)