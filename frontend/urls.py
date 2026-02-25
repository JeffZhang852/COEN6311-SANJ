from django.urls import path

from . import views


urlpatterns = [

    path('', views.home, name='home'),

# Navbar
    path ("services/", views.services, name='services'),
    path ("memberships/", views.memberships, name='memberships'),
    path ("trial/", views.trial, name='trial'),
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

# registration
    path ("register/", views.register_user, name='register'),



]
