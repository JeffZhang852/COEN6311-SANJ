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

# Authentication
   # path('login/', views.login, name='login'),
    #path('signup/', views.signup, name='signup'),
    #path('signed_out/', views.signed_out, name='signed_out'),


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
    path("register/", views.Register.as_view(), name="register")

]
