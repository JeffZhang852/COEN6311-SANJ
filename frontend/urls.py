from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),


    path ("memberships/", views.memberships, name='memberships'),
    path ("nutrition/", views.nutrition, name='nutrition'),


    path ("amenities/", views.amenities, name='amenities'),
    #path ("memberships/", views.memberships, name='memberships'),





    path('gym/', views.gym, name='gym'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('signedout/', views.signed_out, name='signed_out'),
]