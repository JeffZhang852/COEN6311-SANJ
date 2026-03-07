from django.urls import path
from . import views


urlpatterns = [

    path('', views.home, name='home'),

# -----------   Navbar Pages  -----------
    path ("services/", views.services, name='services'),
    path ("memberships/", views.memberships, name='memberships'),
    path("trainers/", views.trainers, name='trainers'),
    path ("nutrition/", views.nutrition, name='nutrition'),

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

# -----------   User Profile & Account   -----------
    path('user_profile/', views.user_profile, name='user_profile'),
    path('update_user/', views.update_user, name='update_user'),
    path('user_account/', views.user_account, name='user_account'),

# -----------   Staff Pages  -----------
    path('staff_login/', views.staff_login, name='staff_login'),
    path('staff_home/', views.staff_home, name='staff_home'),
    path('staff_profile/', views.staff_profile, name='staff_profile'),
    path('members/', views.members, name='members'),
    path('requests/', views.requests, name='requests'),
    path('reports/', views.reports, name='reports'),
    path('messages/', views.private_messages, name='messages'),
    path('articles/', views.articles, name='articles'),
    path('create_article/', views.create_article, name='create_article'),

# path to user profiles from staff_home page
    path("staff/user/<int:user_id>/", views.staff_user_detail, name="staff_user_detail"),
# path to article pages from staff-articles page
    path("staff/article/<int:id>/", views.article_details, name="article_details"),
# path to edit article page from article_details page
    path("staff/article/<int:id>/", views.article_details, name="article_details"),

# -----------   Coach Pages  -----------

    # TODO Newly added.
# Settings user setting. currently only member uses it.
    path('settings/', views.settings_view, name='settings'),

# Coach list
    path('coaches/', views.coach_list_view, name='coach_list'),

# Coach dashboard
    path('coach/dashboard/', views.coach_dashboard, name='coach_dashboard'),
    path('coach/availability/', views.manage_availability, name='manage_availability'),
    path('coach/availability/delete/<int:slot_id>/', views.delete_availability, name='delete_availability'),
    path('coach/appointments/', views.manage_appointments, name='manage_appointments'),

]


