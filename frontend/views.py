from django.shortcuts import render

#new auth
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib import messages

# registration
#django handles the backend database
from .forms import SignUpForm



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


# new User Authentication
def login_user(request):
    if request.method == 'POST':
        #"email" is the "name" in the field
        username = request.POST['username'] # change these to whatever fields put in the form
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You have been logged in')
            return redirect('home') # cant write it as home.html because it's reverse searching for a template with the name "home"
        else:
            messages.success(request, 'Error')
            return redirect('login')
    else:
        return render(request, 'frontend/authentication_templates/login.html') # render the HTML template on first visit


def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('home')


#linked to forms.py
def register_user(request):
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            #login user
            user = authenticate(request, username=username, password=password)
            login(request, user)
            messages.success(request, 'You have registered')
            return redirect('home') # cant write it as home.html because it's reverse searching for a template with the name "home"
        else:
            messages.success(request, 'Error')
            return redirect('register')
    else:
        return render(request, 'frontend/authentication_templates/register.html', {'form': form})




# OLD Authentication
    #change name to login_user when moving it to auth/views.py
#def login1(request):
   # return render(request, 'frontend/authentication_templates/login.html')

#def signed_out(request):
   # return render(request, 'frontend/authentication_templates/signed_out.html')

#def signup(request):
    #return render(request, 'frontend/authentication_templates/signup.html')

