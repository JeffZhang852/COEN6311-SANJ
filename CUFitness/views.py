from django.shortcuts import render

#new auth
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
#   --------- User Permission ---------
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse

from .models import CustomUser,CoachAppointment,CoachAvailability,Equipment_Booking
from .forms import CoachRequestForm, CoachAvailabilityForm, AppointmentRequestForm,AppointmentResponseForm, PrivacySettingsForm


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




# Role checker. Needed to tell which account it is.
def is_member(user):
    return user.is_authenticated and user.role == 'member'

def is_coach(user):
    return user.is_authenticated and user.role == 'coach'

#Not used yet. only coach n member are needed for now
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

# --- Member Views ---
@login_required
@user_passes_test(is_member)
def settings_view(request):
    """Member settings page"""
    """Now has: privacy control and request coach role."""
    privacy_form = PrivacySettingsForm(instance=request.user)
    if request.method == 'POST':
        if 'privacy_submit' in request.POST:
            privacy_form = PrivacySettingsForm(request.POST, instance=request.user)
            if privacy_form.is_valid():
                privacy_form.save()
                messages.success(request, 'Privacy settings updated.')
                return redirect('settings')
        elif 'coach_request_submit' in request.POST:
            # Update coach_request_status to 'pending'
            request.user.coach_request_status = 'pending'
            request.user.save()
            messages.success(request, 'Coach request submitted for approval.')
            return redirect('settings')
    context = {
        'privacy_form': privacy_form,
        'coach_request_status': request.user.coach_request_status,
    }
    return render(request, 'CUFitness/settings.html', context)

@login_required
@user_passes_test(is_member)
def coach_list_view(request):
    """List all approved coaches."""
    coaches = CustomUser.objects.filter(role='coach', is_active=True)


    # TODO need a html page to display the list of coach. change url if necessary

    return render(request, 'CUFitness/coach_list.html', {'coaches': coaches})

# --- Coach Views ---
@login_required
@user_passes_test(is_coach)
def coach_dashboard(request):
    """Overview of coach's appointments and availability."""
    upcoming_appointments = CoachAppointment.objects.filter(
        coach=request.user,
        start_time__gte=timezone.now(),
        status__in=['pending', 'accepted']
    )
    past_appointments = CoachAppointment.objects.filter(
        coach=request.user,
        start_time__lt=timezone.now()
    ).order_by('-start_time')[:10]
    availabilities = CoachAvailability.objects.filter(coach=request.user, start_time__gt=timezone.now())
    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'availabilities': availabilities,
    }

    # TODO New url needed to display coach's availability.

    return render(request, 'CUFitness/coach_dashboard.html', context)

@login_required
@user_passes_test(is_coach)
def manage_availability(request):
    """Add/delete availability slots."""
    if request.method == 'POST':
        form = CoachAvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.coach = request.user
            availability.save()
            messages.success(request, 'Availability slot added.')
            return redirect('manage_availability')
    else:
        form = CoachAvailabilityForm()
    slots = CoachAvailability.objects.filter(coach=request.user).order_by('start_time')
    context = {
        'form': form,
        'slots': slots,
    }

    # TODO New url needed

    return render(request, 'CUFitness/manage_availability.html', context)

@login_required
@user_passes_test(is_coach)
def delete_availability(request, slot_id):
    slot = get_object_or_404(CoachAvailability, id=slot_id, coach=request.user)
    if request.method == 'POST':
        slot.delete()
        messages.success(request, 'Slot deleted.')
    return redirect('manage_availability')

@login_required
@user_passes_test(is_coach)
def manage_appointments(request):
    """View pending appointments and respond."""
    pending = CoachAppointment.objects.filter(coach=request.user, status='pending').order_by('start_time')
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        appointment = get_object_or_404(CoachAppointment, id=appointment_id, coach=request.user)
        form = AppointmentResponseForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Appointment {appointment.status}.')
            return redirect('manage_appointments')
    else:
        form = AppointmentResponseForm()
    context = {
        'pending_appointments': pending,
        'response_form': form,
    }

    # TODO New url needed

    return render(request, 'CUFitness/manage_appointments.html', context)

