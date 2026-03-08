
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.views import generic

from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib import messages

from .models import CustomUser, CoachAppointment, CoachAvailability, EquipmentBooking, Articles
from .forms import CoachRequestForm, CoachAvailabilityForm, AppointmentRequestForm,AppointmentResponseForm, PrivacySettingsForm
from .forms import CustomUserCreationForm, ArticleForm

from django.contrib.auth import update_session_auth_hash
from .forms import UpdateEmailForm, UpdatePasswordForm


User = get_user_model()

# Role checker. Needed to tell which account it is.
def is_member(user):
    return user.is_authenticated and user.role == 'MEMBER'

def is_coach(user):
    return user.is_authenticated and user.role == 'COACH'

def is_staff(user):
    return user.is_authenticated and user.role == 'STAFF'

#Not used yet
def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'



def home(request):
    if request.user.is_authenticated and request.user.role == 'STAFF':

        active_members = CustomUser.objects.filter(
            role="MEMBER",
            is_active=True
        ).order_by("first_name")

        active_coaches = CustomUser.objects.filter(
            role="COACH",
            is_active=True
        ).order_by("first_name")

        context = {
            "active_members": active_members,
            "active_coaches": active_coaches,
        }

        return render(request, "CUFitness/staff_profile/staff_home.html", {"active_members": active_members, "active_coaches": active_coaches})
    else:
        return render(request, 'CUFitness/home.html')

# -----------   Navbar Pages  -----------
def services(request):
    return render(request, 'CUFitness/navbar/services.html')

def memberships(request):
    return render(request, 'CUFitness/navbar/membership.html')

def trainers(request):
    return render(request, 'CUFitness/navbar/trainers.html')

def nutrition(request):
    free_articles = Articles.objects.filter(locked=False)
    locked_articles = Articles.objects.filter(locked=True)
    return render(request, 'CUFitness/navbar/nutrition.html', {"free_articles": free_articles, "locked_articles": locked_articles})

# -----------   Dropdown Menu Pages  -----------
def amenities(request):
    return render(request, 'CUFitness/dropdown/amenities.html')

def schedule(request):
    return render(request, 'CUFitness/dropdown/schedule.html')

def contact(request):
    return render(request, 'CUFitness/dropdown/contact.html')

def about(request):
    return render(request, 'CUFitness/dropdown/about.html')

# -----------   Footer Pages  -----------
def faq(request):
    return render(request, 'CUFitness/faq.html')

def policy(request):
    return render(request, 'CUFitness/policy.html')




# -----------   User Authentication   -----------

class Register(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = "CUFitness/authentication_templates/register.html"

def login_user(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None and (user.role == 'MEMBER' or user.role == 'COACH'):
            login(request, user)
            messages.success(request, 'You have been logged in as ' + user.first_name)
            return redirect('home')
        elif user is not None and user.role == 'STAFF':
            messages.error(request, 'Staff members go to staff login')
            return redirect('staff_login')
        else:
            messages.error(request, 'Invalid Account Email or Password')
            return redirect('login')
    else:
        return render(request, 'CUFitness/authentication_templates/login.html')

def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('home')



# -----------   User Profile & Account   -----------
@login_required(login_url='login')
def user_profile(request):
    return render(request, 'CUFitness/user_profile/user_profile.html')

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_settings(request):
    """Settings page for members and coaches — email, password, privacy, coach request."""
    privacy_form = PrivacySettingsForm(instance=request.user)
    email_form = UpdateEmailForm(instance=request.user)
    password_form = UpdatePasswordForm(user=request.user)

    if request.method == 'POST':

        if 'privacy_submit' in request.POST:
            privacy_form = PrivacySettingsForm(request.POST, instance=request.user)
            if privacy_form.is_valid():
                privacy_form.save()
                messages.success(request, 'Privacy settings updated.')
                return redirect('settings')

        elif 'email_submit' in request.POST:
            email_form = UpdateEmailForm(request.POST, instance=request.user)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, 'Email address updated.')
                return redirect('settings')

        elif 'password_submit' in request.POST:
            password_form = UpdatePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                # keeps the user logged in after a password change -- without that line, Django would log the user out immediately after saving the new password.
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password updated successfully.')
                return redirect('settings')

        elif 'coach_request_submit' in request.POST:
            request.user.coach_request_status = 'PENDING'
            request.user.save()
            messages.success(request, 'Coach request submitted for approval.')
            return redirect('settings')

    context = {
        'privacy_form': privacy_form,
        'email_form': email_form,
        'password_form': password_form,
        'coach_request_status': request.user.coach_request_status,
    }
    return render(request, 'CUFitness/user_profile/settings.html', context)



# -----------   Staff Pages  -----------


def staff_login(request):
    if request.method == 'POST':
        email = request.POST['email'] # change these to whatever fields put in the form
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        # only log in staff members
        if user is not None and user.role == 'STAFF':
            login(request, user)
            # display the first_name of the logged-in user
            messages.success(request, 'You have been logged in as ' + user.first_name)

            return redirect('home') # cant write it as home.html because it's reverse searching for a template with the name "home"
        else:
            messages.error(request, 'Invalid Account Email or Password')
            return redirect('staff_login')
    else:
        return render(request, 'CUFitness/staff_profile/staff_login.html') # render the HTML template on first visit

# prob not needed at this point
# everything is handled through home function
@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def staff_home(request):
    active_members = CustomUser.objects.filter(
        role="MEMBER",
        is_active=True
    ).order_by("first_name")

    print(active_members)

    active_coaches = CustomUser.objects.filter(
        role="COACH",
        is_active=True
    ).order_by("first_name")

    return render(request, "CUFitness/staff_profile/staff_home.html", {"active_members":active_members,"active_coaches":active_coaches})

@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def staff_profile(request):
    return render(request, 'CUFitness/staff_profile/staff_profile.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def staff_settings(request):
    """Settings page for staff — password only."""
    password_form = UpdatePasswordForm(user=request.user)

    if request.method == 'POST':
        if 'password_submit' in request.POST:
            password_form = UpdatePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                # keeps the user logged in after a password change -- without that line, Django would log the user out immediately after saving the new password.
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password updated successfully.')
                return redirect('staff_settings')

    return render(request, 'CUFitness/staff_profile/staff_settings.html', {
        'password_form': password_form,
    })



@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def members(request):
    return render(request, 'CUFitness/staff_profile/members.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def requests(request):
    return render(request, 'CUFitness/staff_profile/requests.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def reports(request):
    return render(request, 'CUFitness/staff_profile/reports.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def private_messages(request):
    return render(request, 'CUFitness/staff_profile/messages.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def staff_user_detail(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    return render(request, "CUFitness/staff_profile/user_detail.html", {
        "user_obj": user_obj
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def articles(request):
    articles = Articles.objects.all()
    return render(request, "CUFitness/staff_profile/articles.html", {"articles":articles})

@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def create_article(request):
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False) #dont immedietly save because we need to add more data to the form (user, author...)
            article.author = request.user
            article.save() # now save everything
            return redirect('articles')
    else:
        form = ArticleForm()
    return render(request, "CUFitness/staff_profile/create_article.html", {"form":form})


def article_details(request, id):
    article = get_object_or_404(Articles, id=id)

    if request.user.is_authenticated:
        base = 'CUFitness/staff_profile/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/base.html'
    else:
        base = 'CUFitness/base.html'

    return render(request, 'CUFitness/staff_profile/article_details.html', {
        'article_obj': article,
        'base_template': base,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def edit_article(request, id):
    article = get_object_or_404(Articles, id=id)
    if request.user != article.author:
        messages.error(request, 'You do not have permission to edit this article.')
        return redirect('articles')
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article updated successfully.')
            return redirect('article_details', id=article.id)
    else:
            form = ArticleForm(instance=article)
    return render(request, 'CUFitness/staff_profile/edit_article.html', {'form': form, 'article': article})

@login_required(login_url='staff_login')
@user_passes_test(is_staff)
def delete_article(request, id):
    article = get_object_or_404(Articles, id=id)

    if request.user != article.author:
        messages.error(request, 'You do not have permission to delete this article.')
        return redirect('articles')

    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted successfully.')
        return redirect('articles')

    return redirect('article_details', id=id)

# ------------------------------------------------------------------


# --- Member Views ---

@login_required(login_url='login')
@user_passes_test(is_member)
def coach_list_view(request):
    """List all approved coaches."""
    coaches = CustomUser.objects.filter(role='COACH', is_active=True)


    # TODO need a html page to display the list of coach. change url if necessary

    return render(request, 'CUFitness/coach_list.html', {'coaches': coaches})

# --- Coach Views ---
@login_required(login_url='login')
@user_passes_test(is_coach)
def coach_dashboard(request):
    """Overview of coach's appointments and availability."""
    upcoming_appointments = CoachAppointment.objects.filter(
        coach=request.user,
        start_time__gte=timezone.now(),
        status__in=['PENDING', 'ACCEPTED']
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

@login_required(login_url='login')
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

@login_required(login_url='login')
@user_passes_test(is_coach)
def delete_availability(request, slot_id):
    slot = get_object_or_404(CoachAvailability, id=slot_id, coach=request.user)
    if request.method == 'POST':
        slot.delete()
        messages.success(request, 'Slot deleted.')
    return redirect('manage_availability')

@login_required(login_url='login')
@user_passes_test(is_coach)
def manage_appointments(request):
    """View pending appointments and respond."""
    pending = CoachAppointment.objects.filter(coach=request.user, status='PENDING').order_by('start_time')
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

