# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- recipe, resources, workout_plans files
- user specific (saved) recipe and workouts pages
- this changelog file
- "create_recipe" staff page
- "edit_recipe" staff page
- "staff_recipes" staff pages
- "recipe_details" for everyone - with access control for locked recipes
- 

### Changed
- nutrition to health_articles
- if author account is deleted for article class, the article is kept and its author is switched to null
- made sure all pages for article.author check for null values

### Fixed
-

### Removed
-

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
