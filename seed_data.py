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
from CUFitness.models import Article, Recipe, RecipeIngredient

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
    author      = coach,
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
    author      = coach,
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

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("\n" + "="*50)
print("✅ Seed complete! Summary:")
print(f"   Users   : {User.objects.count()} total")
print(f"   Articles: {Article.objects.count()} total")
print(f"   Recipes : {Recipe.objects.count()} total")
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