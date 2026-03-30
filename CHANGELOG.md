# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- added coach login option on home page -- for easier testing
- added profile picturefor user/coaches/staff -with default picture- can upload/delete pictures

### Changed
- redesigned the "home" page to fit the theme of the website
- "home" page now displays list of trainers from database
- redesigned the "footer" to fit the theme of the website
- redesigned the "navbar" to fit the theme of the website
- modified the "base.html" to accomodate the changes
- redesigned the "chatbot" page to fit the theme of the website
- redesigned the "privacy policy" page to fit the theme of the website
- redesigned the "services" page to fit the theme of the website
- redesigned the "about" page to fit the theme of the website
- designed the "exercise" page to fit the theme of the website -- filter doesnt work right now
- redesigned the "amenities" page with copy-rigth free images
- redesigned the "login" page (user/coach/staff)
- redesigned the "create_account" page to fit the theme of the website
- redesigned the "profile" page (user, coach/staff)
- "user_profile" now correctly pulls and displays upcoming/past/canceled user appointments
- redesigned the "user_inbox" page to fit the theme of the website
- redesigned the "user_calendar" page to fit the theme of the website
- redesigned the "user_settings" page to fit the theme of the website
- re-arranged some of the (html/css) files into sub-directories

### Fixed
-

### Removed
- removed unused/old HTML files (old login/register files)
- removed "staff_home" page (urls & views.py) (kept html file) - "home" handles auth & redirects
- removed "memberships" page (html/css/URLS/views.py) -- same info is on home page
- removed "trainers" page (html/css/URLS/views.py) -- same info is on home page
- removed "members" page (html/css/URLS/views.py) from "staff_home" - same info is on home page
- removed un-needed tests
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
