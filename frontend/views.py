from django.shortcuts import render



#Navbar
def home(request):
    return render(request, 'frontend/home.html')


def memberships(request):
    return render(request, 'frontend/membership.html')

def trainers(request):
    return render(request, 'frontend/trainers.html')

def nutrition(request):
    return render(request, 'frontend/nutrition.html')


#Dropdown menu
def amenities(request):
    return render(request, 'frontend/amenities.html')

def schedule(request):
    return render(request, 'frontend/schedule.html')

def contact(request):
    return render(request, 'frontend/contact.html')
def about(request):
    return render(request, 'frontend/about.html')





def gym(request):
    return render(request, 'frontend/gym.html')




#Registration
def login(request):
    return render(request, 'authentication/login.html')

def signed_out(request):
    return render(request, 'authentication/signed_out.html')

def signup(request):
    return render(request, 'authentication/signup.html')

