# CUFitness/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token   # optional – only if you enable token auth
from . import views

# ---- REST API Router ----
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'availabilities', views.CoachAvailabilityViewSet)
router.register(r'appointments', views.CoachAppointmentViewSet)
router.register(r'articles', views.ArticleViewSet)
router.register(r'recipes', views.RecipeViewSet)
router.register(r'workouts', views.WorkoutPlanViewSet)
router.register(r'exercises', views.ExerciseViewSet)
router.register(r'messages', views.MessageViewSet)
router.register(r'challenges', views.ChallengeViewSet)
router.register(r'challenge-participations', views.ChallengeParticipationViewSet)
router.register(r'gym-info', views.GymInfoViewSet)

urlpatterns = [

# region General Website Navigation
    path('', views.home, name='home'),
    path("services/", views.services, name='services'),

    # -----------   Resources-Dropdown Pages  -----------
    path("articles/", views.user_articles, name='user_articles'),
    path("recipes/", views.user_recipes, name='user_recipes'),
    path("workout_plans/", views.workout_plans, name='workout_plans'),
    path("exercises/", views.user_exercises, name='user_exercises'),
    path("challenges/", views.user_challenges, name='user_challenges'),
    path('fitness_assistant/', views.chatbot, name='chatbot'),

    # -----------   More-Tab Dropdown Pages  ----------
    path("amenities/", views.amenities, name='amenities'),
    path("schedule/", views.gym_schedule, name='gym_schedule'),
    path("contact/", views.contact_us, name='contact_us'),
    path("about/", views.about, name='about'),

    # -----------   Footer Pages  -----------
    path("faq/", views.faq, name='faq'),
    path("privacy_policy/", views.privacy_policy, name='privacy_policy'),
# endregion

# region User Authentication
    path("register/", views.Register.as_view(), name="register"),
    path("login/", views.login_user, name='login'),
    path("coach login/", views.coach_login, name='coach_login'),
    path('logout/', views.logout_user, name='logout'),
# endregion

# region Logged-In User Pages
    path('user profile/', views.user_profile, name='user_profile'),
    path("user profile/upload_picture/", views.upload_picture, name='upload_picture'),
    path('user profile/delete-picture/', views.delete_picture, name='delete_picture'),
    path('user settings/', views.user_settings, name='user_settings'),
    path('user inbox/', views.user_inbox, name='user_inbox'),
    path('user calendar/', views.user_calendar, name='user_calendar'),
    path('user saved recipes/', views.user_saved_recipes, name='user_saved_recipes'),
    path('user saved workouts/', views.user_saved_workouts, name='user_saved_workouts'),
# endregion

# region Staff/Employee Pages
    path('staff_login/', views.staff_login, name='staff_login'),
    path('staff_profile/', views.staff_profile, name='staff_profile'),
    path('coach_requests/', views.coach_requests, name='coach_requests'),
    path('staff_reports/', views.staff_reports, name='staff_reports'),
    path('staff_messages/', views.staff_messages, name='staff_messages'),
    path('staff_settings/', views.staff_settings, name='staff_settings'),
    # path to user profiles from staff_home page
    path("staff_user_details/<int:user_id>/", views.staff_user_details, name="staff_user_details"),

    # region Article Pages
    path("article_details/<int:id>/", views.article_details, name="article_details"),
 # -----------  Staff Article Pages  -----------
    path('staff_articles/', views.staff_articles, name='staff_articles'),
    path('staff_create_article/', views.staff_create_article, name='staff_create_article'),
    # path to edit article page from article_details page
    path("staff_edit_article/<int:id>/edit/", views.staff_edit_article, name="staff_edit_article"),
    path("staff_delete_article/<int:id>/delete/", views.staff_delete_article, name="staff_delete_article"),
    # endregion

    # region Recipe Pages
    path("recipe_details/<int:id>/", views.recipe_details, name="recipe_details"),
# -----------  Staff Recipe Pages  -----------
    path("staff_recipes/", views.staff_recipes, name='staff_recipes'),
    path('staff_create_recipe/', views.staff_create_recipe, name='staff_create_recipe'),
    # path to edit recipe page from recipe_details page
    path("staff_edit_recipe/<int:id>/edit/", views.staff_edit_recipe, name="staff_edit_recipe"),
    path("staff_delete_recipe/<int:id>/delete/", views.staff_delete_recipe, name="staff_delete_recipe"),
    # endregion

    # region Exercise Pages
    path("exercise_details/<int:id>/", views.exercise_details, name="exercise_details"),
# -----------   Exercise Pages  -----------
    path("staff_exercises/", views.staff_exercises, name='staff_exercises'),
    path('create_exercises/', views.create_exercises, name='create_exercises'),
    # path to edit exercise page from exercise_details page
    path("exercise/<int:id>/edit/", views.edit_exercise, name="edit_exercise"),
    path("exercise/<int:id>/delete/", views.delete_exercise, name="delete_exercise"),
    # endregion

    # region Workout-Plans Pages
    path("workout_plan_details/<int:id>/", views.workout_plan_details, name="workout_plan_details"),
    # -----------  Staff Workout Pages  -----------
    path("staff_workouts/", views.staff_workouts, name='staff_workouts'),
    path('staff_create_workout/', views.staff_create_workout, name='staff_create_workout'),
    # path to edit workout page from workout_details page
    path("staff_edit_workout/<int:id>/edit/", views.staff_edit_workout, name="staff_edit_workout"),
    path("staff_delete_workout/<int:id>/delete/", views.staff_delete_workout, name="staff_delete_workout"),
    # endregion

    # region Challenges Pages
    path("challenge_details/<int:id>/", views.challenge_details, name="challenge_details"),
    # -----------  Staff Challenges Pages  -----------
    path("staff_challenges/", views.staff_challenges, name='staff_challenges'),
    path("create_challenge/", views.create_challenge, name='create_challenge'),
    path("edit_challenge/<int:id>/", views.edit_challenge, name="edit_challenge"),
    path("delete_challenge/<int:id>/", views.delete_challenge, name="delete_challenge"),
    # -----------  System Challenges Pages  -----------
    path("join_challenge/<int:challenge_id>/", views.join_challenge, name='join_challenge'),
    path("update_progress/<int:participation_id>/", views.update_progress, name='update_progress'),
    # endregion

# endregion



#  ----------- Appointment api (obsolete, kept for reference) ----------
    # -----------   Coach Schedule & Availability AJAX   -----------
    path('user_coach_schedule/', views.user_coach_schedule, name='user_coach_schedule'),
    path('api/availability/add/', views.ajax_add_availability, name='ajax_add_availability'),
    path('api/availability/<int:slot_id>/edit/', views.ajax_edit_availability, name='ajax_edit_availability'),
    path('api/availability/<int:slot_id>/delete/', views.ajax_delete_availability, name='ajax_delete_availability'),
    path('api/availability/<uuid:group_id>/cancel_series/', views.ajax_cancel_series, name='ajax_cancel_series'),
    path('api/coaches/', views.api_coaches, name='api_coaches'),
    path('api/coach-availability/', views.api_coach_availability, name='api_coach_availability'),
    path('api/all-availability/', views.api_all_availability, name='api_all_availability'),
    path('api/request-appointment/', views.api_request_appointment, name='api_request_appointment'),
    path('api/appointment/<int:appointment_id>/accept/', views.ajax_accept_appointment, name='ajax_accept_appointment'),
    path('api/appointment/<int:appointment_id>/reject/', views.ajax_reject_appointment, name='ajax_reject_appointment'),


# -----------   Coach Request Handling  -----------
    path("staff/coach-request/<int:user_id>/", views.handle_coach_request, name="handle_coach_request"),

# -----------   Coach Pages (legacy, might be merged) -----------
    # Coach list
    #path('coaches/', views.coach_list_view, name='coach_list'),
    # Coach dashboard (legacy)
    path('coach/dashboard/', views.coach_dashboard, name='coach_dashboard'),
    path('coach/availability/', views.manage_availability, name='manage_availability'),
    path('coach/availability/delete/<int:slot_id>/', views.delete_availability, name='delete_availability'),
    path('coach/appointments/', views.manage_appointments, name='manage_appointments'),

    # Messaging
    path('api/coaches/search/', views.api_coach_search, name='api_coach_search'),
    path('send_message/', views.send_message, name='send_message'),
    path('reply_message/<int:message_id>/', views.reply_message, name='reply_message'),
    path('mark_read/<int:message_id>/', views.mark_read, name='mark_read'),

    # ----- REST API endpoints -----
    path('api/', include(router.urls)),
    # Browsable API login/logout
    path('api-auth/', include('rest_framework.urls')),
    # Optional: token authentication endpoint (if you decide to enable it later)
    # path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
]