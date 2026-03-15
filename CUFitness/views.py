from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.http import HttpResponseNotAllowed

from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib import messages

from .models import CustomUser, CoachAppointment, CoachAvailability, EquipmentBooking, Article, Recipe, RecipeIngredient
from .forms import CoachRequestForm, CoachAvailabilityForm, AppointmentRequestForm,AppointmentResponseForm, PrivacySettingsForm
from .forms import CustomUserCreationForm, ArticleForm, RecipeForm, IngredientFormSet

from django.contrib.auth import update_session_auth_hash
from .forms import UpdateEmailForm, UpdatePasswordForm

# for calendar;
from django.http import JsonResponse
import json as _json
import json
from django.db import transaction

User = get_user_model()

# Role checker. Needed to tell which account it is.
def is_member(user):
    return user.is_authenticated and user.role == 'MEMBER'

def is_coach(user):
    return user.is_authenticated and user.role == 'COACH'

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

def is_admin_user(user):
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

        return render(request, "CUFitness/staff/staff_home.html", {"active_members": active_members, "active_coaches": active_coaches})
    else:
        return render(request, 'CUFitness/home.html')

# region all navbar pages
# -----------   Navbar Pages  -----------
def services(request):
    return render(request, 'CUFitness/navbar/services.html')

def memberships(request):
    return render(request, 'CUFitness/navbar/membership.html')


#   TODO make it member only view, remove it from navbar options
def trainers(request):
    return render(request, 'CUFitness/navbar/trainers.html')


def user_articles(request):
    free_articles = Article.objects.filter(locked=False)
    locked_articles = Article.objects.filter(locked=True)
    return render(request, 'CUFitness/navbar/user_articles.html', {"free_articles": free_articles, "locked_articles": locked_articles})

def workout_plans(request):
    return render(request, 'CUFitness/navbar/workout_plans.html')

def user_recipes(request):
    free_recipes = Recipe.objects.filter(locked=False)
    locked_recipes = Recipe.objects.filter(locked=True)
    return render(request, "CUFitness/navbar/user_recipes.html", {"free_recipes": free_recipes, "locked_recipes": locked_recipes})


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
# endregion


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
                return redirect('user_settings')

        elif 'email_submit' in request.POST:
            email_form = UpdateEmailForm(request.POST, instance=request.user)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, 'Email address updated.')
                return redirect('user_settings')

        elif 'password_submit' in request.POST:
            password_form = UpdatePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                # keeps the user logged in after a password change -- without that line, Django would log the user out immediately after saving the new password.
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password updated successfully.')
                return redirect('user_settings')

# server-side check to prevent multiple submissions
        elif 'coach_request_submit' in request.POST:
            if request.user.coach_request_status in ('NONE', 'REJECTED'):
                request.user.coach_request_status = 'PENDING'
                request.user.save()
                messages.success(request, 'Coach request submitted for approval.')
            else:
                messages.error(request, 'You already have an active or approved request.')
            return redirect('user_settings')

    context = {
        'privacy_form': privacy_form,
        'email_form': email_form,
        'password_form': password_form,
        'coach_request_status': request.user.coach_request_status,
    }
    return render(request, 'CUFitness/user_profile/settings.html', context)

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_inbox(request):
    return render(request, 'CUFitness/user_profile/user_inbox.html')

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_calendar(request):
    """
     Calendar page for members and coaches.

     Members  → see their upcoming coach appointments (accepted & pending).
     Coaches  → see their upcoming appointments *and* ALL their availability slots
                (past + future) so the calendar can render them for editing.
     """
    now = timezone.now()

    if is_member(request.user):
        upcoming_appointments = CoachAppointment.objects.filter(
            member=request.user,
            start_time__gte=now,
            status__in=['PENDING', 'ACCEPTED'],
        ).select_related('coach').order_by('start_time')

        past_appointments = CoachAppointment.objects.filter(
            member=request.user,
            start_time__lt=now,
        ).select_related('coach').order_by('-start_time')[:10]

        availabilities = []

    else:  # COACH
        upcoming_appointments = CoachAppointment.objects.filter(
            coach=request.user,
            start_time__gte=now,
            status__in=['PENDING', 'ACCEPTED'],
        ).select_related('member').order_by('start_time')

        past_appointments = CoachAppointment.objects.filter(
            coach=request.user,
            start_time__lt=now,
        ).select_related('member').order_by('-start_time')[:10]

        # ALL slots (past + future) so coaches can see/edit their full history
        availabilities = CoachAvailability.objects.filter(
            coach=request.user,
        ).order_by('start_time')

    # ── Build calendar event JSON ──────────────────────────────────
    calendar_events = []

    for appt in upcoming_appointments:
        label = (
            f"Session with {appt.member.first_name} {appt.member.last_name}"
            if is_coach(request.user)
            else f"Session with Coach {appt.coach.first_name} {appt.coach.last_name}"
        )
        color = '#15803d' if appt.status == 'ACCEPTED' else '#b45309'
        calendar_events.append({
            'type': 'appointment',
            'title': label,
            'start': appt.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': appt.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'color': color,
            'status': appt.status,
        })

    for slot in availabilities:
        calendar_events.append({
            'type': 'availability',
            'id': slot.id,
            'title': 'Open Slot' if not slot.is_booked else 'Booked Slot',
            'start': slot.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': slot.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'color': '#1d4ed8' if not slot.is_booked else '#6b7280',
            'status': 'AVAILABLE' if not slot.is_booked else 'BOOKED',
            'is_booked': slot.is_booked,
        })

    # Upcoming open slots for the sidebar list
    upcoming_availabilities = [s for s in availabilities if s.start_time >= now and not s.is_booked]

    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'availabilities': upcoming_availabilities,
        'calendar_events_json': json.dumps(calendar_events),
        'is_coach': is_coach(request.user),
    }
    return render(request, 'CUFitness/user_profile/user_calendar.html', context)

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_saved_recipes(request):
    return render(request, 'CUFitness/user_profile/user_saved_recipes.html')

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_saved_workouts(request):
    return render(request, 'CUFitness/user_profile/user_saved_workouts.html')


# calendar
# ── AJAX: add availability slot ───────────────────────────────────
@login_required(login_url='login')
@user_passes_test(is_coach)
def ajax_add_availability(request):
    """POST {start_time, end_time} → create slot, return JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data = _json.loads(request.body)
    form = CoachAvailabilityForm(data)
    if form.is_valid():
        slot = form.save(commit=False)
        slot.coach = request.user
        try:
            slot.save()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        return JsonResponse({
            'id':    slot.id,
            'start': slot.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end':   slot.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
        })
    return JsonResponse({'error': form.errors.as_json()}, status=400)

@login_required(login_url='login')
@user_passes_test(is_coach)
def ajax_edit_availability(request, slot_id):
    """POST {start_time, end_time} → update slot, return JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    slot = get_object_or_404(CoachAvailability, id=slot_id, coach=request.user)
    if slot.is_booked:
        return JsonResponse({'error': 'Cannot edit a booked slot.'}, status=400)

    data = _json.loads(request.body)
    form = CoachAvailabilityForm(data, instance=slot)
    if form.is_valid():
        try:
            form.save()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        return JsonResponse({
            'id':    slot.id,
            'start': slot.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end':   slot.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
        })
    return JsonResponse({'error': form.errors.as_json()}, status=400)

@login_required(login_url='login')
@user_passes_test(is_coach)
def ajax_delete_availability(request, slot_id):
    """POST → delete slot, return JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    slot = get_object_or_404(CoachAvailability, id=slot_id, coach=request.user)
    if slot.is_booked:
        return JsonResponse({'error': 'Cannot delete a booked slot.'}, status=400)
    slot.delete()
    return JsonResponse({'deleted': slot_id})


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
        return render(request, 'CUFitness/staff/staff_login.html') # render the HTML template on first visit

# prob not needed at this point
# everything is handled through home function
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_home(request):
    active_members = CustomUser.objects.filter(
        role="MEMBER",
        is_active=True
    ).order_by("first_name")

    active_coaches = CustomUser.objects.filter(
        role="COACH",
        is_active=True
    ).order_by("first_name")

    return render(request, "CUFitness/staff/staff_home.html", {"active_members":active_members,"active_coaches":active_coaches})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_profile(request):
    return render(request, 'CUFitness/staff/staff_profile.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
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

    return render(request, 'CUFitness/staff/staff_settings.html', {
        'password_form': password_form,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def members(request):
    return render(request, 'CUFitness/staff/members.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def coach_requests(request):
    pending = CustomUser.objects.filter(coach_request_status='PENDING')
    approved = CustomUser.objects.filter(coach_request_status='APPROVED')
    rejected = CustomUser.objects.filter(coach_request_status='REJECTED')
    return render(request, 'CUFitness/staff/coach_requests.html', {
        'pending_requests': pending,
        'approved_requests': approved,
        'rejected_requests': rejected,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def handle_coach_request(request, user_id):
    """
    Staff-only. Approve or reject a member's coach request.
    Expects a POST with 'action' = 'APPROVED' or 'REJECTED'.
    Approving also promotes the user's role from MEMBER → COACH.
    """
    if request.method != 'POST':
        return redirect('coach_requests')

    member = get_object_or_404(CustomUser, id=user_id)

    # Safety check: only act on users who have actually submitted a request
    if member.coach_request_status not in ('PENDING', 'REJECTED'):
        messages.error(request, 'This user does not have an active coach request.')
        return redirect('coach_requests')

    action = request.POST.get('action')

    if action == 'APPROVED':
        member.coach_request_status = 'APPROVED'
        member.role = 'COACH'        # promote the account
        member.save()
        messages.success(
            request,
            f'{member.first_name} {member.last_name} has been approved and promoted to Coach. They will need to log out and back in for changes to take effect.'
        )

    elif action == 'REJECTED':
        member.coach_request_status = 'REJECTED'
        # role stays MEMBER
        member.save()
        messages.success(
            request,
            f'{member.first_name} {member.last_name}\'s coach request has been rejected.'
        )

    else:
        messages.error(request, 'Invalid action.')

    return redirect('coach_requests')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_reports(request):
    return render(request, 'CUFitness/staff/staff_reports.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_messages(request):
    return render(request, 'CUFitness/staff/staff_messages.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_user_detail(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    return render(request, "CUFitness/staff/user_detail.html", {
        "user_obj": user_obj
    })


# region Staff Articles
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_articles(request):
    articles = Article.objects.all()
    return render(request, "CUFitness/staff/articles/staff_articles.html", {"articles":articles})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def create_article(request):
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False) #dont immedietly save because we need to add more data to the form (user, author...)
            article.author = request.user
            article.save() # now save everything
            return redirect('staff_articles')
    else:
        form = ArticleForm()
    return render(request, "CUFitness/staff/articles/create_article.html", {"form":form})

def article_details(request, id):
    article = get_object_or_404(Article, id=id)

    if request.user.is_authenticated:
        base = 'CUFitness/staff/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/base.html'
    else:
        base = 'CUFitness/base.html'

# make sure user can't enter the url manually to access the locked articles
# An unauthenticated user can directly hit the URL for a locked/premium article and read it without this checker.
    if article.locked and not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'CUFitness/staff/articles/article_details.html', {
        'article_obj': article,
        'base_template': base,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def edit_article(request, id):
    article = get_object_or_404(Article, id=id)
    if request.user != article.author:
        messages.error(request, 'You do not have permission to edit this article.')
        return redirect('staff_articles')
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article updated successfully.')
            return redirect('article_details', id=article.id)
    else:
        form = ArticleForm(instance=article)
    return render(request, 'CUFitness/staff/articles/edit_article.html', {'form': form, 'article': article})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def delete_article(request, id):
    article = get_object_or_404(Article, id=id)

    if request.user != article.author:
        messages.error(request, 'You do not have permission to delete this article.')
        return redirect('staff_articles')

    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted successfully.')
        return redirect('staff_articles')

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    return redirect('article_details', id=id)
# endregion


# region Staff Recipes
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_recipes(request):
    recipes = Recipe.objects.all()
    return render(request, "CUFitness/staff/recipes/staff_recipes.html", {"recipes":recipes})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def create_recipe(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        formset = IngredientFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()

            formset.instance = recipe  # link ingredients to the recipe
            formset.save()
            return redirect('recipe_details', id=recipe.id)
    else:
        form = RecipeForm()
        formset = IngredientFormSet()

    return render(request, 'CUFitness/staff/recipes/create_recipe.html', {'form': form, 'formset': formset})

def recipe_details(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    #the following is needed to get the "display" tags, since multiselectfield doesn't have that functionality by default unlike charfield
    # Build a lookup dict from the choices and map the stored codes to labels
    choices_dict = dict(Recipe.DIETARY_CHOICES)
    dietary_display = [choices_dict.get(code, code) for code in recipe.dietary_restrictions]

    if request.user.is_authenticated:
        base = 'CUFitness/staff/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/base.html'
    else:
        base = 'CUFitness/base.html'

        # make sure user can't enter the url manually to access the locked recipes
        # An unauthenticated user can directly hit the URL for a locked/premium article and read it without this checker.
    if recipe.locked and not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'CUFitness/staff/recipes/recipe_details.html', {
        'recipe_obj': recipe,
        'dietary_display': dietary_display,
        'base_template': base,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def edit_recipe(request, id):
    recipe = get_object_or_404(Recipe, id=id)

    if request.user != recipe.author:
        messages.error(request, 'You do not have permission to edit this recipe.')
        return redirect('staff_recipes')

    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        formset = IngredientFormSet(request.POST, instance=recipe)  # ✅ instance added

        if form.is_valid() and formset.is_valid():           # ✅ both validated
            form.save()
            formset.save()
            messages.success(request, 'Recipe updated successfully.')
            return redirect('recipe_details', id=recipe.id)
    else:
        form = RecipeForm(instance=recipe)
        formset = IngredientFormSet(instance=recipe)         # ✅ GET uses instance, not POST

    return render(request, 'CUFitness/staff/recipes/edit_recipe.html', {
        'form': form,
        'formset': formset,   # ✅ formset passed to template
        'recipe': recipe,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def delete_recipe(request, id):
    recipe = get_object_or_404(Recipe, id=id)

    if request.user != recipe.author:
        messages.error(request, 'You do not have permission to delete this recipe.')
        return redirect('staff_recipes')

    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe deleted successfully.')
        return redirect('staff_recipes')

    return HttpResponseNotAllowed(['POST'])
# endregion


# region Staff Workouts
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_workouts(request):
    return render(request, 'CUFitness/staff/workout_plans/staff_workouts.html')

def workout_details(request, id):
    return render(request, 'CUFitness/staff/workout_plans/workout_details.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def create_workouts(request):
    return render(request, 'CUFitness/staff/workout_plans/create_workouts.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def edit_workout(request, id):
    return render(request, 'CUFitness/staff/workout_plans/edit_workout.html')
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def delete_workout(request, id):
    return render(request, 'CUFitness/staff/workout_plans/delete_workout.html')
# endregion


# region Staff Exercises
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_exercises(request):
    return render(request, 'CUFitness/staff/exercises/staff_exercises.html')

def exercise_details(request, id):
    return render(request, 'CUFitness/staff/exercises/exercise_details.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def create_exercises(request):
    return render(request, 'CUFitness/staff/exercises/create_exercise.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def edit_exercise(request, id):
    return render(request, 'CUFitness/staff/exercises/edit_exercise.html')
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def delete_exercise(request, id):
    return render(request, 'CUFitness/staff/exercises/delete_exercise.html')
# endregion




# ------------------------------------------------------------------




# --- Member Views ---

@login_required(login_url='login')
@user_passes_test(is_member)
def coach_list_view(request):
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
    pending = (CoachAppointment.objects.filter
               (coach=request.user,
                status='PENDING'
                ).order_by('start_time')).select_related('member') # Without (select_related('member')), accessing appointment.member.first_name in the template triggers an extra query per row (N+1).

    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')

        try:
            with transaction.atomic():
                # lock this row until the request completes
                appointment = CoachAppointment.objects.select_for_update().get(
                    id=appointment_id,
                    coach=request.user
                )
                form = AppointmentResponseForm(request.POST, instance=appointment)
                if form.is_valid():
                    form.save()  # clean() runs here, safely locked
                    messages.success(request, f'Appointment {appointment.status}.')
                    return redirect('manage_appointments')
        except CoachAppointment.DoesNotExist:
            messages.error(request, 'Appointment not found.')
            return redirect('manage_appointments')

    else:
        form = AppointmentResponseForm()

    context = {
        'pending_appointments': pending,
        'response_form': form,
    }
    return render(request, 'CUFitness/manage_appointments.html', context)