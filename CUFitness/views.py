from django.shortcuts import render

#new auth
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib import messages

#   --------- User Permission ---------
from django.contrib.auth.decorators import login_required, permission_required




# registration
#django handles the backend database
#   --------- OLD -- NOT USED---------
#from .forms import SignUpForm

# new user model
from django.urls import reverse_lazy
from django.views import generic
from .forms import CustomUserCreationForm
from django.contrib.auth import get_user_model
User = get_user_model()



#   --------- Calendar ---------


def home(request):
    return render(request, 'CUFitness/home.html')


# Navbar Pages
def services(request):
    return render(request, 'CUFitness/navbar/services.html')

def memberships(request):
    return render(request, 'CUFitness/navbar/membership.html')

def trainers(request):
    return render(request, 'CUFitness/navbar/trainers.html')

def nutrition(request):
    return render(request, 'CUFitness/navbar/nutrition.html')


# Dropdown Menu Pages
def amenities(request):
    return render(request, 'CUFitness/dropdown/amenities.html')

def schedule(request):
    return render(request, 'CUFitness/dropdown/schedule.html')

def contact(request):
    return render(request, 'CUFitness/dropdown/contact.html')

def about(request):
    return render(request, 'CUFitness/dropdown/about.html')


# Footer Pages
def faq(request):
    return render(request, 'CUFitness/faq.html')

def policy(request):
    return render(request, 'CUFitness/policy.html')


# User Authentication
def login_user(request):
    if request.method == 'POST':
        email = request.POST['email'] # change these to whatever fields put in the form
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            # display the first_name of the logged-in user
            messages.success(request, 'You have been logged in as ' + User.objects.get(email=email).first_name)

            return redirect('home') # cant write it as home.html because it's reverse searching for a template with the name "home"
        else:
            messages.success(request, 'Error')
            return redirect('login')
    else:
        return render(request, 'CUFitness/authentication_templates/login.html') # render the HTML template on first visit

def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('home')


#   --------- OLD -- NOT USED---------
'''
# linked to forms.py
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
        return render(request, 'CUFitness/authentication_templates/register.html', {'form': form})
'''

# ------------------------------------------------------------------
#   --------- User ---------
@login_required(login_url='login')
def user_profile(request):
    return render(request, 'CUFitness/user_profile/user_profile.html')

# linked to forms.py
@login_required(login_url='login')
def update_user(request):
    pass
@login_required(login_url='login')
def user_account(request):
    return render(request, 'CUFitness/user_profile/user_account.html')

# ------------------------------------------------------------------
#   --------- Staff ---------

def staff_login(request):
    return render(request, 'CUFitness/staff_profile/staff_login.html')

def staff_home(request):
    return render(request, 'CUFitness/staff_profile/staff_home.html')

def staff_profile(request):
    return render(request, 'CUFitness/staff_profile/staff_profile.html')

def members(request):
    return render(request, 'CUFitness/staff_profile/members.html')

def requests(request):
    return render(request, 'CUFitness/staff_profile/requests.html')

def reports(request):
    return render(request, 'CUFitness/staff_profile/reports.html')

def private_messages(request):
    return render(request, 'CUFitness/staff_profile/messages.html')


# ------------------------------------------------------------------
#########
# new user model
#########
# add auto login after successful registration
# add ability to change role on sign up
class Register(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = "CUFitness/authentication_templates/register.html"

#   --------- Calendar ---------
