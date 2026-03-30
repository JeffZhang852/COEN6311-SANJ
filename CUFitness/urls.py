from django.urls import path
from . import views


urlpatterns = [

    path('', views.home, name='home'),

# -----------   Navbar Pages  -----------
    path("services/", views.services, name='services'),
    path("articles/", views.user_articles, name='user_articles'),
    path("workout_plans/", views.workout_plans, name='workout_plans'),
    path("user_recipes/", views.user_recipes, name='user_recipes'),
    #path("user_workouts/", views.user_workouts, name='user_workouts'),
    path("user_exercises/", views.user_exercises, name='user_exercises'),


# -----------   Dropdown Menu Pages  -----------
    path("amenities/", views.amenities, name='amenities'),
    path("schedule/", views.schedule, name='schedule'),
    path("contact/", views.contact, name='contact'),
    path("about/", views.about, name='about'),

# -----------   Footer Pages  -----------
    path("faq/", views.faq, name='faq'),
    path("policy/", views.policy, name='policy'),

# -----------   User Authentication   -----------
    path("register/", views.Register.as_view(), name="register"),
    path("login/", views.login_user, name='login'),
    path("coach_login/", views.coach_login, name='coach_login'),
    path('logout/', views.logout_user, name='logout'),

# -----------   User Profile & Settings   -----------
    path('user_profile/', views.user_profile, name='user_profile'),
    path("user_profile/upload_picture/", views.upload_picture, name='upload_picture'),
    path('user_profile/delete-picture/', views.delete_picture, name='delete_picture'),

    path('user_settings/', views.user_settings, name='user_settings'),
    path('user_inbox/', views.user_inbox, name='user_inbox'),
    path('user_calendar/', views.user_calendar, name='user_calendar'),
    path('user_saved_recipes/', views.user_saved_recipes, name='user_saved_recipes'),
    path('user_saved_workouts/', views.user_saved_workouts, name='user_saved_workouts'),


# -----------   Staff Pages  -----------
    path('staff_login/', views.staff_login, name='staff_login'),
    path('staff_profile/', views.staff_profile, name='staff_profile'),
    path('coach_requests/', views.coach_requests, name='coach_requests'),
    path('staff_reports/', views.staff_reports, name='staff_reports'),
    path('staff_messages/', views.staff_messages, name='staff_messages'),
    path('staff_settings/', views.staff_settings, name='staff_settings'),

# path to user profiles from staff_home page
    path("staff_user_detail/<int:user_id>/", views.staff_user_detail, name="staff_user_detail"),


# -----------   Article Pages  -----------
    path('staff_articles/', views.staff_articles, name='staff_articles'),
    path('create_article/', views.create_article, name='create_article'),
    # path to article pages from staff-articles page
    path("article_details/<int:id>/", views.article_details, name="article_details"),
    # path to edit article page from article_details page
    path("edit_article/<int:id>/edit/", views.edit_article, name="edit_article"),
    path("delete_article/<int:id>/delete/", views.delete_article, name="delete_article"),

# -----------   Recipe Pages  -----------
    path("staff_recipes/", views.staff_recipes, name='staff_recipes'),
    path('create_recipe/', views.create_recipe, name='create_recipe'),
    # path to article pages from staff-articles page
    path("recipe_details/<int:id>/", views.recipe_details, name="recipe_details"),
    # path to edit article page from article_details page
    path("recipe/<int:id>/edit/", views.edit_recipe, name="edit_recipe"),
    path("recipe/<int:id>/delete/", views.delete_recipe, name="delete_recipe"),

# -----------   Workout Pages  -----------
    path("staff_workouts/", views.staff_workouts, name='staff_workouts'),
    path('create_workouts/', views.create_workouts, name='create_workouts'),
    # path to article pages from staff-articles page
    path("workout_details/<int:id>/", views.workout_details, name="workout_details"),
    # path to edit article page from article_details page
    path("workout/<int:id>/edit/", views.edit_workout, name="edit_workout"),
    path("workout/<int:id>/delete/", views.delete_workout, name="delete_workout"),

# -----------   Exercise Pages  -----------
    path("staff_exercises/", views.staff_exercises, name='staff_exercises'),
    path('create_exercises/', views.create_exercises, name='create_exercises'),
    # path to article pages from staff-articles page
    path("exercise_details/<int:id>/", views.exercise_details, name="exercise_details"),
    # path to edit article page from article_details page
    path("exercise/<int:id>/edit/", views.edit_exercise, name="edit_exercise"),
    path("exercise/<int:id>/delete/", views.delete_exercise, name="delete_exercise"),


# -----------   Chatbot Pages  -----------
    path('chatbot/', views.chatbot, name='chatbot'),

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
]