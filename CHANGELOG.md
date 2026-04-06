# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added


### Changed
- redesigned the "staff_settings" page - can only update password
- designed the "staff_profile" page - can only upload/remove profile picture
- desgined the "staff_exercises" page
- designed the "staff_edit_challenge" page
- re-formatted the test file
- display coach rating & reviews on "home" page
- display coach rating & reviews on "staff_home" page
- display coach rating & reviews on "staff_user_details" page
- designed the "staff_create_exercise" page
- designed the "staff_edit_exercise" page
- designed the "staff_create_workout" page
- designed the "staff_edit_workout" page
- redesigned the "coach_profile" page
- redesgined "coach_settings" page
- designed "coach_home" page
- redesigned the "coach_schedule" page
- updated seed_data file
- updated test file

### Fixed
- Coach role locked out of user login, now gets proper re-directories
- challenge_details now only accessible to authenticated users - special decorator
- update_progress now rejects negative increments — progress can't go below 0
- staff_create_exercise doesn't assign non-existent field created_by anymore
- content where the author's account was deleted is editable/deletable by any staff member instead of being permanently locked.
- Coach edit/delete functionality in "coach_schedule" are now working correctly
- 8 total issues/bugs in appointment AJAX/API functions:

	- "ajax_edit_availability" hours check bug when "open 24hrs"
	- "ajax_delete_availability" hours check bug when "open 24hrs"

	- "ajax_edit_availability" — now correctly checks hours naive local time vs. aware datetime
	- "api_request_appointment" — Race condition / no atomic transaction (Two requests for the same slot can 
			pass the is_booked=False check and both create appointments) -- now locks the row until full completion
			
	- "ajax_reject_appointment" - now correctly sets availability to None after freeing it
	- "ajax_cancel_appointment"- "get_object_or_404" would not trigger the "except" block just raises "Http404"
			- now correctly raises "DoesNotExist" which triggers the "except" block
	
	- "CoachReviewViewSet.perform_create" raises "PermissionError" (500) instead of DRF ValidationError or PermissionDenied
			- now correctly uses PermissionDenied (403) and DRFValidationError (400)
			
	-"ajax_add_availability" - Overlapping check for recurring slots only excludes unbooked slots
			- removed "is_booked=False" -> now checks for booked and unbooked slots

### Removed
- removed the "user_saved_workouts" page (urls/views/html/css)
- removed the "user_saved_recipes" page (urls/views/html/css)
- removed old "articles.css" file
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
