from django.urls import path

from . import views


urlpatterns = [

    path('', views.home, name='home'),

# Navbar
    path ("services/", views.services, name='services'),
    path ("memberships/", views.memberships, name='memberships'),
    path("trainers/", views.trainers, name='trainers'),
    path ("nutrition/", views.nutrition, name='nutrition'),
    path ("amenities/", views.amenities, name='amenities'),

# Dropdown menu
    path ("amenities/", views.amenities, name='amenities'),
    path ("schedule/", views.schedule, name='schedule'),
    path ("contact/", views.contact, name='contact'),
    path ("about/", views.about, name='about'),

#faq
    path("faq/", views.faq, name='faq'),

# new auth section
    path ("login/", views.login_user, name='login'),
    path ('logout/', views.logout_user, name='logout'),

# -----------   OLD -----------
    # registration
    #path ("register/", views.register_user, name='register'),


# User Profile
    path('user_profile/', views.user_profile, name='user_profile'),
    path('update_user/', views.update_user, name='update_user'),

# user account
    path('user_account/', views.user_account, name='user_account'),


# -----------   NEW    -----------
# new user model and registration form
    path("register/", views.Register.as_view(), name="register"),



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


