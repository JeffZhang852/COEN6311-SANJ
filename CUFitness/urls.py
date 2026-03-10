from django.urls import path
from . import views


urlpatterns = [

    path('', views.home, name='home'),

# -----------   Navbar Pages  -----------
    path ("services/", views.services, name='services'),
    path ("memberships/", views.memberships, name='memberships'),
    path("trainers/", views.trainers, name='trainers'),

    path("resources/", views.resources, name='resources'),
    path ("health_articles/", views.health_articles, name='health_articles'),
    path("workout_plans/", views.workout_plans, name='workout_plans'),
    path("recipes/", views.recipes, name='recipes'),


# -----------   Dropdown Menu Pages  -----------
    path ("amenities/", views.amenities, name='amenities'),
    path ("schedule/", views.schedule, name='schedule'),
    path ("contact/", views.contact, name='contact'),
    path ("about/", views.about, name='about'),

# -----------   Footer Pages  -----------
    path("faq/", views.faq, name='faq'),
    path("policy/", views.policy, name='policy'),

# -----------   User Authentication   -----------
    path("register/", views.Register.as_view(), name="register"),
    path ("login/", views.login_user, name='login'),
    path ('logout/', views.logout_user, name='logout'),

# -----------   User Profile & Settings   -----------
    path('user_profile/', views.user_profile, name='user_profile'),
    path('user_settings/', views.user_settings, name='settings'),
    path('user_inbox/', views.user_inbox, name='user_inbox'),
    path('user_calendar/', views.user_calendar, name='user_calendar'),
    path('user_recipes/', views.user_recipes, name='user_recipes'),
    path('user_workouts/', views.user_workouts, name='user_workouts'),


# -----------   Staff Pages  -----------
    path('staff_login/', views.staff_login, name='staff_login'),
    path('staff_home/', views.staff_home, name='staff_home'),
    path('staff_profile/', views.staff_profile, name='staff_profile'),
    path('members/', views.members, name='members'),
    path('coach_requests/', views.coach_requests, name='coach_requests'),
    path('reports/', views.reports, name='reports'),
    path('messages/', views.private_messages, name='messages'),
    path('staff_settings/', views.staff_settings, name='staff_settings'),

# path to user profiles from staff_home page
    path("staff_user_detail/<int:user_id>/", views.staff_user_detail, name="staff_user_detail"),


    path("resource_management/", views.resource_management, name='resource_management'),

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

   #path("staff_workouts/", views.staff_workouts, name='staff_workouts'),
    #path('create_workouts/', views.create_workouts, name='create_workouts'),
    # path to article pages from staff-articles page
   # path("workout_details/<int:id>/", views.workout_details, name="workout_details"),
    # path to edit article page from article_details page
   # path("workout/<int:id>/edit/", views.edit_workout, name="edit_workout"),
   # path("workout/<int:id>/delete/", views.delete_workout, name="delete_workout"),




# Calendar AJAX endpoints (availability add / edit / delete)
    path('api/availability/add/', views.ajax_add_availability, name='ajax_add_availability'),
    path('api/availability/<int:slot_id>/edit/', views.ajax_edit_availability, name='ajax_edit_availability'),
    path('api/availability/<int:slot_id>/delete/', views.ajax_delete_availability, name='ajax_delete_availability'),


# -----------   Coach Request Handling  -----------
    path("staff/coach-request/<int:user_id>/", views.handle_coach_request, name="handle_coach_request"),  # NEW

# -----------   Coach Pages  -----------

# Coach list
    path('coaches/', views.coach_list_view, name='coach_list'),

# Coach dashboard
    path('coach/dashboard/', views.coach_dashboard, name='coach_dashboard'),
    path('coach/availability/', views.manage_availability, name='manage_availability'),
    path('coach/availability/delete/<int:slot_id>/', views.delete_availability, name='delete_availability'),
    path('coach/appointments/', views.manage_appointments, name='manage_appointments'),

]


