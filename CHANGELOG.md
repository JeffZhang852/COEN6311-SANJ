# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- 	Contac_us:
	- ContactMessage model -> migrations
	- ContactMessageForm
	- designed contact_us page
	- designed staff-facing support messages page
	- register model in admin

### Changed
- redesigned the "challenges" page to fit the theme - landing page to encourage registration
- designed "challenge_details" page to fit the theme
- redesigned the "gym_schedule" page to display gym schedule
- designed the "exercise_details" page to fit the theme
- "challenges" are now clickable -> "challenge_details"
- added back button to "article_details" page
- designed "workout_plans" page to fit the theme
- edited the "GymInfo" model to have "open 24hrs" as option - open 24hrs except weekends
- created/designed the "workout_plan_details" page
- added back button to "recipe_details" page
- redesigned the "staff_home" page
- redesigned the "user_details" page
- redesigned the "staff_create_article" page
- redesigned the "staff_edit_article" page
- redesigned the "staff_create_recipe" page
- redesigned the "staff_edit_recipe" page
- designed the "staff_workouts" page
- "seed_data.py" now also populates the gym schedule
- re-arranged some of the urls to fit into folding regions

### Fixed

### Removed
- deleted extra "user_inbox" function in views.py
- removed the "filter" from the "articles" page - not working anyways - they are not in model
---

## [0.1.0] - 2026-03-10

### Added
- 

---

<!-- 
INSTRUCTIONS
============
Before each commit or release, open this file in your editor and:

1. Move items from [Unreleased] into a new versioned section:
   ## [1.2.3] - YYYY-MM-DD

2. Use these change categories (delete any that are empty):
   Added     — new features
   Changed   — changes to existing functionality
   Deprecated — soon-to-be removed features
   Removed   — removed features
   Fixed     — bug fixes
   Security  — vulnerability patches

3. Keep [Unreleased] at the top, always ready for the next batch of changes.

VERSION BUMP GUIDE (Semantic Versioning)
  MAJOR (1.x.x) — breaking changes
  MINOR (x.1.x) — new features, backwards-compatible
  PATCH (x.x.1) — bug fixes, backwards-compatible
-->
