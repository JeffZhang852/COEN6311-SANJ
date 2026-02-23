from django.shortcuts import render



def home(request):
    return render(request, 'frontend/home.html')


# Navbar
def services(request):
    return render(request, 'frontend/navbar/services.html')

def memberships(request):
    return render(request, 'frontend/navbar/membership.html')

def trial(request):
    return render(request, 'frontend/navbar/trial.html')

def trainers(request):
    return render(request, 'frontend/navbar/trainers.html')

def nutrition(request):
    return render(request, 'frontend/navbar/nutrition.html')


# Dropdown menu
def amenities(request):
    return render(request, 'frontend/dropdown/amenities.html')

def schedule(request):
    return render(request, 'frontend/dropdown/schedule.html')

def contact(request):
    return render(request, 'frontend/dropdown/contact.html')

def about(request):
    return render(request, 'frontend/dropdown/about.html')





def gym(request):
    return render(request, 'frontend/gym.html')




# Authentication
def login(request):
    return render(request, 'authentication/login.html')

def signed_out(request):
    return render(request, 'authentication/signed_out.html')

def signup(request):
    return render(request, 'authentication/signup.html')

