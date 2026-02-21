from django.shortcuts import render



# Create your views here.
def home(request):
    return render(request, 'frontend/home.html')

def test(request):
    return render(request, 'test.html')

def gym(request):
    return render(request, 'frontend/gym.html')


def memberships(request):
    return render(request, 'frontend/membership.html')

def login(request):
    return render(request, 'authentication/login.html')

def signed_out(request):
    return render(request, 'authentication/signed_out.html')

def signup(request):
    return render(request, 'authentication/signup.html')

