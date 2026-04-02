# Third-party
from datetime import datetime, timedelta, timezone as dt_timezone
import json
import torch
import uuid

# Django
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

# Django REST API
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

# Local import
from .forms import (
    ArticleForm, ChallengeForm, ContactMessageForm, CustomUserCreationForm,
    IngredientFormSet, PrivacySettingsForm, ProfilePictureForm, RecipeForm,
    UpdateEmailForm, UpdatePasswordForm
)
from .models import (
    Article, Challenge, ChallengeParticipation, CoachAppointment, CoachAvailability,
    CoachReview, ContactMessage, CustomUser, EquipmentList, Exercise, GymInfo,
    Message, Recipe, WorkoutPlan, WorkoutPlanExercise
)
from .serializers import (
    CoachReviewSerializer, UserSerializer
)

User = get_user_model()

# =================================================================================================================
# ================================================ UTILITY ========================================================
# =================================================================================================================

# Timezone helpers
def to_local_time(dt):
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    return dt.astimezone(timezone.get_current_timezone())

def local_date_to_utc_range(date_str):
    local_tz = timezone.get_current_timezone()
    local_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    start_local = datetime.combine(local_date, datetime.min.time())
    end_local = start_local + timedelta(days=1)
    start_utc = timezone.make_aware(start_local, local_tz).astimezone(dt_timezone.utc)
    end_utc = timezone.make_aware(end_local, local_tz).astimezone(dt_timezone.utc)
    return start_utc, end_utc

# Role checkers
def is_member(user):
    return user.is_authenticated and user.role == 'MEMBER'

def is_coach(user):
    return user.is_authenticated and user.role == 'COACH'

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

def is_admin_user(user):
    return user.is_authenticated and user.role == 'ADMIN'


# =================================================================================================================
# ================================================== USER =========================================================
# =================================================================================================================

# region ----------- User Authentication -----------
class Register(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = "CUFitness/general_website/authentication/register.html"

def login_user(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None and (user.role == 'MEMBER'):
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
        return render(request, 'CUFitness/general_website/authentication/login.html')

def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('home')

def coach_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None and user.role == 'COACH':
            login(request, user)
            messages.success(request, 'You have been logged in as ' + user.first_name)
            return redirect('home')
        else:
            messages.error(request, 'Invalid Account Email or Password')
            return redirect('coach_login')
    else:
        return render(request, 'CUFitness/coach/coach_login.html')
# endregion

# region ----------- User Profile & Account -----------
@login_required(login_url='login')
def user_profile(request):
    if is_coach(request.user):
        return redirect('coach_profile')
    now = timezone.now()
    appointments = CoachAppointment.objects.filter(member=request.user).select_related('coach').order_by('start_time')
    upcoming_appointments = appointments.filter(start_time__gte=now).exclude(status='CANCELLED')
    past_appointments = appointments.filter(start_time__lt=now)
    canceled_appointments = appointments.filter(status='CANCELLED')
    context = {
        "upcoming_appointments": upcoming_appointments,
        "past_appointments": past_appointments,
        "canceled_appointments": canceled_appointments,
    }
    return render(request, 'CUFitness/user/user_profile.html', context)

@login_required(login_url='login')
@require_POST
def upload_picture(request):
    form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
    return redirect('user_profile')

@login_required(login_url='login')
@require_POST
def delete_picture(request):
    user = request.user
    if user.profile_picture and user.profile_picture.name != 'defaults/Default_Profile_Picture.jpg':
        user.profile_picture.delete(save=False)
    user.profile_picture = 'defaults/Default_Profile_Picture.jpg'
    user.save()
    return redirect('user_profile')

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_settings(request):
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
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password updated successfully.')
                return redirect('user_settings')
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
    return render(request, 'CUFitness/user/user_settings.html', context)

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_inbox(request):
    return render(request, 'CUFitness/user/user_inbox.html')

@login_required(login_url='login')
def user_calendar(request):
    if is_coach(request.user):
        return redirect('user_coach_schedule')
    now = timezone.now()
    upcoming_appointments = CoachAppointment.objects.filter(
        member=request.user,
        start_time__gte=now,
        status__in=['PENDING', 'ACCEPTED'],
    ).select_related('coach').order_by('start_time')
    past_appointments = CoachAppointment.objects.filter(
        member=request.user,
        start_time__lt=now,
    ).select_related('coach').order_by('-start_time')[:10]
    for appt in past_appointments:
        appt.can_review = (appt.status == 'ACCEPTED' and not hasattr(appt, 'review'))
        appt.has_review = hasattr(appt, 'review')
    calendar_events = []
    for appt in upcoming_appointments:
        appt.can_review = (appt.status == 'ACCEPTED' and not hasattr(appt, 'review'))
        appt.has_review = hasattr(appt, 'review')
        label = f"Session with Coach {appt.coach.first_name} {appt.coach.last_name}"
        color = '#15803d' if appt.status == 'ACCEPTED' else '#b45309'
        calendar_events.append({
            'type': 'appointment',
            'title': label,
            'start': appt.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': appt.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'color': color,
            'status': appt.status,
        })
    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'calendar_events_json': json.dumps(calendar_events),
        'is_coach': False,
    }
    return render(request, 'CUFitness/user/user_calendar.html', context)

@login_required(login_url='login')
@user_passes_test(is_coach)
def user_coach_schedule(request):
    now = timezone.now()
    confirmed = CoachAppointment.objects.filter(
        coach=request.user,
        start_time__gte=now,
        status='ACCEPTED'
    ).select_related('member').order_by('start_time')
    pending = CoachAppointment.objects.filter(
        coach=request.user,
        status='PENDING'
    ).select_related('member').order_by('start_time')
    upcoming_avail = CoachAvailability.objects.filter(
        coach=request.user,
        start_time__gte=now,
        start_time__lte=now + timedelta(days=14),
        is_booked=False
    ).order_by('start_time')
    gym_info = {}
    for i in range(14):
        day = (now + timedelta(days=i)).date()
        weekday = day.weekday()
        try:
            g = GymInfo.objects.get(day=weekday)
            gym_info[day.isoformat()] = {
                'is_open': g.is_open,
                'open_time': g.open_time.isoformat() if g.open_time else None,
                'close_time': g.close_time.isoformat() if g.close_time else None,
            }
        except GymInfo.DoesNotExist:
            gym_info[day.isoformat()] = {'is_open': False}
    calendar_events = []
    for appt in confirmed:
        calendar_events.append({
            'type': 'appointment',
            'title': f"Session with {appt.member.first_name}",
            'start': appt.start_time.isoformat(),
            'end': appt.end_time.isoformat(),
            'color': '#15803d',
            'status': 'ACCEPTED',
        })
    for slot in upcoming_avail:
        calendar_events.append({
            'type': 'availability',
            'id': slot.id,
            'title': 'Open Slot',
            'start': slot.start_time.isoformat(),
            'end': slot.end_time.isoformat(),
            'color': '#1d4ed8',
            'is_booked': False,
            'is_recurring': slot.is_recurring,
            'recurrence_group': str(slot.recurrence_group) if slot.recurrence_group else None,
        })
    context = {
        'confirmed': confirmed,
        'pending': pending,
        'upcoming_avail': upcoming_avail,
        'calendar_events_json': json.dumps(calendar_events),
        'gym_settings': json.dumps(gym_info),
    }
    return render(request, 'CUFitness/user/user_coach_schedule.html', context)

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_saved_recipes(request):
    return render(request, 'CUFitness/user/user_saved_recipes.html')

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_saved_workouts(request):
    return render(request, 'CUFitness/user/user_saved_workouts.html')
# endregion

# region ----------- Coach Views -----------
@login_required(login_url='login')
@user_passes_test(is_coach)
def coach_dashboard(request):
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
    return render(request, 'CUFitness/coach_dashboard.html', context)

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
def coach_profile_page(request):
    return render(request, 'CUFitness/coach/coach_profile.html')
# endregion

# region ----------- Staff Views -----------
def staff_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None and user.role == 'STAFF':
            login(request, user)
            messages.success(request, 'You have been logged in as ' + user.first_name)
            return redirect('home')
        else:
            messages.error(request, 'Invalid Account Email or Password')
            return redirect('staff_login')
    else:
        return render(request, 'CUFitness/staff/staff_login.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_profile(request):
    return render(request, 'CUFitness/staff/staff_profile.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_settings(request):
    password_form = UpdatePasswordForm(user=request.user)
    if request.method == 'POST':
        if 'password_submit' in request.POST:
            password_form = UpdatePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password updated successfully.')
                return redirect('staff_settings')
    return render(request, 'CUFitness/staff/staff_settings.html', {'password_form': password_form})

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
    if request.method != 'POST':
        return redirect('coach_requests')
    member = get_object_or_404(CustomUser, id=user_id)
    if member.coach_request_status not in ('PENDING', 'REJECTED'):
        messages.error(request, 'This user does not have an active coach request.')
        return redirect('coach_requests')
    action = request.POST.get('action')
    if action == 'APPROVED':
        member.coach_request_status = 'APPROVED'
        member.role = 'COACH'
        member.save()
        messages.success(request, f'{member.first_name} {member.last_name} has been approved and promoted to Coach. They will need to log out and back in for changes to take effect.')
    elif action == 'REJECTED':
        member.coach_request_status = 'REJECTED'
        member.save()
        messages.success(request, f'{member.first_name} {member.last_name}\'s coach request has been rejected.')
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
    all_messages = ContactMessage.objects.all()
    if request.method == 'POST':
        msg_id = request.POST.get('msg_id')
        ContactMessage.objects.filter(id=msg_id).update(is_read=True)
        return redirect('contact_inbox')
    return render(request, 'CUFitness/staff/staff_messages.html', {'messages': all_messages})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_user_details(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    return render(request, "CUFitness/staff/staff_user_details.html", {"user_obj": user_obj})

# Staff Articles
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_articles(request):
    articles = Article.objects.all()
    return render(request, "CUFitness/staff/articles/staff_articles.html", {"articles": articles})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_create_article(request):
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            return redirect('staff_articles')
    else:
        form = ArticleForm()
    return render(request, "CUFitness/staff/articles/staff_create_article.html", {"form": form})

def article_details(request, id):
    article = get_object_or_404(Article, id=id)
    if request.user.is_authenticated:
        base = 'CUFitness/staff/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/general_website/base.html'
    else:
        base = 'CUFitness/general_website/base.html'
    if article.locked and not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'CUFitness/staff/articles/article_details.html', {
        'article_obj': article,
        'base_template': base,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_edit_article(request, id):
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
    return render(request, 'CUFitness/staff/articles/staff_edit_article.html', {'form': form, 'article': article})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_delete_article(request, id):
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

# Staff Recipes
def recipe_details(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    choices_dict = dict(Recipe.DIETARY_CHOICES)
    dietary_display = [choices_dict.get(code, code) for code in recipe.dietary_restrictions]
    if request.user.is_authenticated:
        base = 'CUFitness/staff/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/general_website/base.html'
    else:
        base = 'CUFitness/general_website/base.html'
    if recipe.locked and not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'CUFitness/staff/recipes/recipe_details.html', {
        'recipe_obj': recipe,
        'dietary_display': dietary_display,
        'base_template': base,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_recipes(request):
    recipes = Recipe.objects.all()
    return render(request, "CUFitness/staff/recipes/staff_recipes.html", {"recipes": recipes})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_create_recipe(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        formset = IngredientFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            formset.instance = recipe
            formset.save()
            return redirect('recipe_details', id=recipe.id)
    else:
        form = RecipeForm()
        formset = IngredientFormSet()
    return render(request, 'CUFitness/staff/recipes/staff_create_recipe.html', {'form': form, 'formset': formset})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_edit_recipe(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    if request.user != recipe.author:
        messages.error(request, 'You do not have permission to edit this recipe.')
        return redirect('staff_recipes')
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        formset = IngredientFormSet(request.POST, instance=recipe)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Recipe updated successfully.')
            return redirect('recipe_details', id=recipe.id)
    else:
        form = RecipeForm(instance=recipe)
        formset = IngredientFormSet(instance=recipe)
    return render(request, 'CUFitness/staff/recipes/staff_edit_recipe.html', {
        'form': form,
        'formset': formset,
        'recipe': recipe,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_delete_recipe(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    if request.user != recipe.author:
        messages.error(request, 'You do not have permission to delete this recipe.')
        return redirect('staff_recipes')
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe deleted successfully.')
        return redirect('staff_recipes')
    return HttpResponseNotAllowed(['POST'])

# Staff Workouts
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_workouts(request):
    all_workout_plans = WorkoutPlan.objects.all()
    return render(request, 'CUFitness/staff/workout_plans/staff_workouts.html', {'workout_plans': all_workout_plans})

def workout_plan_details(request, id):
    workout_plan = get_object_or_404(WorkoutPlan, id=id)
    if request.user.is_authenticated:
        base = 'CUFitness/staff/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/general_website/base.html'
    else:
        base = 'CUFitness/general_website/base.html'
    if workout_plan.locked and not request.user.is_authenticated:
        return redirect('login')
    exercises = workout_plan.exercises.select_related('exercise').order_by('order')
    return render(request, 'CUFitness/staff/workout_plans/workout_plan_details.html', {
        'workout_plan': workout_plan,
        'exercises': exercises,
        'base_template': base,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_create_workout(request):
    return render(request, 'CUFitness/staff/workout_plans/staff_create_workout.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_edit_workout(request, id):
    return render(request, 'CUFitness/staff/workout_plans/staff_edit_workout.html')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_delete_workout(request, id):
    return render(request, 'CUFitness/staff/workout_plans/delete_workout.html')

# Staff Exercises
def exercise_details(request, id):
    exercise = get_object_or_404(Exercise, id=id)
    if request.user.is_authenticated:
        base = 'CUFitness/staff/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/general_website/base.html'
    else:
        base = 'CUFitness/general_website/base.html'
    return render(request, 'CUFitness/staff/exercises/exercise_details.html', {
        'exercise_obj': exercise,
        'base_template': base,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_exercises(request):
    return render(request, 'CUFitness/staff/exercises/staff_exercises.html')

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


# =================================================================================================================
# ============================================== FUNCTIONALITY ====================================================
# =================================================================================================================

# region ----------- Navbar Pages -----------
def home(request):
    if request.user.is_authenticated and request.user.role == 'STAFF':
        active_members = CustomUser.objects.filter(role="MEMBER", is_active=True).order_by("first_name")
        active_coaches = CustomUser.objects.filter(role="COACH", is_active=True).order_by("first_name")
        return render(request, "CUFitness/staff/staff_home.html",
                      {"active_members": active_members, "active_coaches": active_coaches})
    else:
        active_coaches = CustomUser.objects.filter(role="COACH", is_active=True).order_by("first_name")
        return render(request, 'CUFitness/general_website/home.html', {"active_coaches": active_coaches})

def services(request):
    equipment = EquipmentList.objects.filter(is_active=True).order_by('name')
    total_items = sum(e.quantity for e in equipment)
    context = {
        'equipment_list': equipment,
        'total_equipment_items': total_items,
    }
    return render(request, 'CUFitness/general_website/navbar/services.html', context)

def user_articles(request):
    free_articles = Article.objects.filter(locked=False)
    locked_articles = Article.objects.filter(locked=True)
    return render(request, 'CUFitness/general_website/navbar/articles.html',
                  {"free_articles": free_articles, "locked_articles": locked_articles})

def workout_plans(request):
    free_workouts = WorkoutPlan.objects.filter(locked=False).prefetch_related('exercises')
    locked_workouts = WorkoutPlan.objects.filter(locked=True).prefetch_related('exercises')
    return render(request, 'CUFitness/general_website/navbar/workout_plans.html', {
        'free_workouts': free_workouts,
        'locked_workouts': locked_workouts,
    })

def user_recipes(request):
    free_recipes = Recipe.objects.filter(locked=False)
    locked_recipes = Recipe.objects.filter(locked=True)
    return render(request, "CUFitness/general_website/navbar/recipes.html",
                  {"free_recipes": free_recipes, "locked_recipes": locked_recipes})

def user_exercises(request):
    exercises = Exercise.objects.all().order_by('muscle_group')
    return render(request, "CUFitness/general_website/navbar/exercises.html", {"exercises": exercises})

def user_challenges(request):
    if request.user.is_authenticated:
        challenges = Challenge.objects.all()
        user_participation = ChallengeParticipation.objects.filter(user=request.user)
        joined_ids = user_participation.values_list('challenge_id', flat=True)
        leaderboard_data = []
        for challenge in Challenge.objects.all():
            participants_qs = ChallengeParticipation.objects.filter(challenge=challenge)
            participants = participants_qs.select_related('user').order_by('-progress')[:5]
            top_participants = participants_qs.select_related('user').order_by('-progress')[:5]
            leaderboard_data.append({
                'challenge': challenge,
                'participants': participants,
                'top_participants': top_participants,
                'count': participants_qs.count()
            })
        return render(request, 'CUFitness/general_website/navbar/challenges.html', {
            'leaderboard_data': leaderboard_data,
            'challenges': challenges,
            'joined_ids': joined_ids,
            'participations': user_participation,
        })
    else:
        return render(request, 'CUFitness/general_website/navbar/challenges.html')

@ensure_csrf_cookie
def chatbot(request):
    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)
        from CUFitness.apps import get_chatbot_model
        tokenizer, model = get_chatbot_model()
        messages = [{"role": "user", "content": user_message}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1
            )
        new_tokens = outputs[0][inputs['input_ids'].shape[1]:]
        reply = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        if not reply:
            reply = "I'm not sure how to answer that."
        return JsonResponse({'reply': reply})
    return render(request, 'CUFitness/general_website/chatbot.html')
# endregion

# region ----------- Dropdown Menu Pages -----------
def amenities(request):
    return render(request, 'CUFitness/general_website/dropdown/amenities.html')

def gym_schedule(request):
    schedule = GymInfo.objects.all().order_by('day')
    return render(request, 'CUFitness/general_website/dropdown/gym_schedule.html', {"gym_schedule": schedule})

def contact_us(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent!')
            return redirect('contact_us')
    else:
        form = ContactMessageForm()
    return render(request, 'CUFitness/general_website/dropdown/contact_us.html', {"form": form})

def about(request):
    return render(request, 'CUFitness/general_website/dropdown/about.html')
# endregion

# region ----------- Footer Pages -----------
def faq(request):
    return render(request, 'CUFitness/general_website/faq.html')

def privacy_policy(request):
    return render(request, 'CUFitness/general_website/privacy_policy.html')
# endregion

# region ----------- Fitness Challenges -----------
@login_required(login_url='login')
def join_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    ChallengeParticipation.objects.get_or_create(user=request.user, challenge=challenge)
    return redirect('user_challenges')

@login_required(login_url='login')
def update_progress(request, participation_id):
    participation = get_object_or_404(ChallengeParticipation, id=participation_id, user=request.user)
    if request.method == "POST":
        increment = int(request.POST.get('progress', 0))
        participation.progress += increment
        if participation.progress > participation.challenge.goal_target:
            participation.progress = participation.challenge.goal_target
        participation.save()
        participation.refresh_from_db()
    return redirect('user_challenges')

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def create_challenge(request):
    if request.method == "POST":
        form = ChallengeForm(request.POST)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.created_by = request.user
            challenge.save()
            return redirect('staff_challenges')
    else:
        form = ChallengeForm()
    return render(request, 'CUFitness/staff/challenges/create_challenge.html', {'form': form})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_challenges(request):
    challenges = Challenge.objects.all()
    return render(request, 'CUFitness/staff/challenges/challenges.html', {'challenges': challenges})

@user_passes_test(lambda user: is_member(user) or is_coach(user) or is_staff_user(user))
def challenge_details(request, id):
    challenge = get_object_or_404(Challenge, id=id)
    if request.user.is_authenticated:
        base = 'CUFitness/staff/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/general_website/base.html'
    else:
        base = 'CUFitness/general_website/base.html'
    participants = ChallengeParticipation.objects.filter(challenge=challenge).select_related('user').order_by('-progress')
    is_joined = request.user.is_authenticated and ChallengeParticipation.objects.filter(user=request.user, challenge=challenge).exists()
    return render(request, 'CUFitness/staff/challenges/challenge_details.html', {
        'challenge': challenge,
        'participants': participants,
        'base_template': base,
        'is_joined': is_joined,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def edit_challenge(request, id):
    challenge = get_object_or_404(Challenge, id=id)
    if request.method == 'POST':
        form = ChallengeForm(request.POST, instance=challenge)
        if form.is_valid():
            form.save()
            messages.success(request, 'Challenge updated successfully.')
            return redirect('challenge_details', id=challenge.id)
    else:
        form = ChallengeForm(instance=challenge)
    return render(request, 'CUFitness/staff/challenges/create_challenge.html', {'form': form, 'challenge': challenge})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def delete_challenge(request, id):
    challenge = get_object_or_404(Challenge, id=id)
    if request.method == 'POST':
        challenge.delete()
        messages.success(request, 'Challenge deleted successfully.')
        return redirect('staff_challenges')
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    return redirect('challenge_details', id=id)
# endregion


# =================================================================================================================
# ==================================================== API ========================================================
# =================================================================================================================

# region ----------- REST API (Django REST Framework) -----------
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return CustomUser.objects.none()
        if is_staff_user(user):
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=user.id)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='coach-profile', permission_classes=[IsAuthenticated])
    def coach_profile(self, request, pk=None):
        coach = self.get_object()
        if coach.role != 'COACH':
            return Response({'detail': 'User is not a coach.'}, status=status.HTTP_400_BAD_REQUEST)
        avg_rating = coach.average_rating()
        total_reviews = coach.total_reviews_count()
        latest_reviews = coach.latest_reviews(limit=5)
        hourly_salary = 15 + (2 * avg_rating)
        total_hours_month = coach.total_accepted_hours_current_month()
        estimated_monthly_payout = total_hours_month * hourly_salary
        reviews_data = CoachReviewSerializer(latest_reviews, many=True, context={'request': request}).data
        data = {
            'average_rating': avg_rating,
            'total_reviews': total_reviews,
            'latest_reviews': reviews_data,
            'hourly_salary': round(hourly_salary, 2),
            'total_hours_this_month': round(total_hours_month, 1),
            'estimated_monthly_payout': round(estimated_monthly_payout, 2)
        }
        return Response(data)

    def perform_update(self, serializer):
        if not is_staff_user(self.request.user):
            serializer.save(role=self.get_object().role)
        else:
            serializer.save()

class CoachReviewViewSet(viewsets.ModelViewSet):
    queryset = CoachReview.objects.all()
    serializer_class = CoachReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['coach', 'member', 'rating']

    def get_queryset(self):
        user = self.request.user
        if is_staff_user(user):
            return CoachReview.objects.all()
        elif is_coach(user):
            return CoachReview.objects.filter(coach=user)
        elif is_member(user):
            return CoachReview.objects.filter(member=user)
        return CoachReview.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not is_member(user):
            raise PermissionError("Only members can write reviews.")
        appointment_id = self.request.data.get('appointment')
        if not appointment_id:
            raise PermissionError("Appointment ID is required.")
        try:
            appointment = CoachAppointment.objects.get(id=appointment_id)
        except CoachAppointment.DoesNotExist:
            raise PermissionError("Appointment not found.")
        if appointment.member != user:
            raise PermissionError("You can only review your own appointments.")
        if appointment.status != 'ACCEPTED':
            raise PermissionError("You can only review accepted appointments.")
        if hasattr(appointment, 'review'):
            raise PermissionError("This appointment has already been reviewed.")
        serializer.save(member=user, coach=appointment.coach, appointment=appointment)

# endregion

# region ----------- AJAX / Appointment API -----------
@login_required(login_url='login')
@user_passes_test(is_coach)
@require_POST
@ensure_csrf_cookie
def ajax_add_availability(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    slots_data = data.get('slots', [])
    recurrence = data.get('recurrence', 'none')
    recurrence_weeks = data.get('recurrence_weeks', 0)
    if not slots_data:
        return JsonResponse({'error': 'No slots provided'}, status=400)
    if recurrence not in ('none', 'weeks', 'indefinite'):
        return JsonResponse({'error': 'Invalid recurrence value'}, status=400)
    if recurrence == 'weeks' and (not isinstance(recurrence_weeks, int) or recurrence_weeks < 1):
        return JsonResponse({'error': 'recurrence_weeks must be a positive integer'}, status=400)
    created_slots = []
    recurrence_group = None
    if recurrence != 'none':
        recurrence_group = uuid.uuid4()
    max_weeks = 0
    if recurrence == 'weeks':
        max_weeks = recurrence_weeks
    elif recurrence == 'indefinite':
        max_weeks = 52
    now = timezone.now()
    gym_info_cache = {}
    for i in range(7):
        try:
            gym_info_cache[i] = GymInfo.objects.get(day=i)
        except GymInfo.DoesNotExist:
            gym_info_cache[i] = None
    for slot_info in slots_data:
        start_str = slot_info.get('start')
        end_str = slot_info.get('end')
        if not start_str or not end_str:
            return JsonResponse({'error': 'Missing start or end in slot'}, status=400)
        try:
            start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt, timezone.utc)
            if timezone.is_naive(end_dt):
                end_dt = timezone.make_aware(end_dt, timezone.utc)
        except ValueError:
            return JsonResponse({'error': 'Invalid datetime format in slot'}, status=400)
        local_start = to_local_time(start_dt)
        local_end = to_local_time(end_dt)
        if start_dt < now:
            return JsonResponse({'error': f'Slot {start_dt} is in the past'}, status=400)
        if (end_dt - start_dt) != timedelta(hours=1):
            return JsonResponse({'error': 'Each slot must be exactly one hour'}, status=400)
        weekday = local_start.weekday()
        gym = gym_info_cache.get(weekday)
        if not gym or not gym.is_open:
            return JsonResponse({'error': f'Gym closed on {local_start.strftime("%A")}'}, status=400)
        if local_start.time() < gym.open_time or local_end.time() > gym.close_time:
            return JsonResponse({'error': f'Slot {local_start.time()} outside gym hours'}, status=400)
        if recurrence == 'none':
            overlapping = CoachAvailability.objects.filter(
                coach=request.user,
                start_time__lt=end_dt,
                end_time__gt=start_dt,
                is_booked=False
            )
            if overlapping.exists():
                return JsonResponse({'error': f'Slot {start_dt} overlaps existing availability'}, status=400)
            slot = CoachAvailability(
                coach=request.user,
                start_time=start_dt,
                end_time=end_dt,
                is_recurring=False
            )
            slot.save()
            created_slots.append(slot)
        else:
            for week in range(max_weeks):
                slot_start = start_dt + timedelta(weeks=week)
                slot_end = end_dt + timedelta(weeks=week)
                if CoachAvailability.objects.filter(coach=request.user, start_time=slot_start, end_time=slot_end).exists():
                    continue
                overlapping = CoachAvailability.objects.filter(
                    coach=request.user,
                    start_time__lt=slot_end,
                    end_time__gt=slot_start,
                    is_booked=False
                )
                if overlapping.exists():
                    continue
                slot = CoachAvailability(
                    coach=request.user,
                    start_time=slot_start,
                    end_time=slot_end,
                    is_recurring=True,
                    recurrence_group=recurrence_group
                )
                slot.save()
                created_slots.append(slot)
    return JsonResponse({'created': len(created_slots), 'recurrence_group': str(recurrence_group) if recurrence_group else None})

@login_required(login_url='login')
@user_passes_test(is_coach)
def ajax_edit_availability(request, slot_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    slot = get_object_or_404(CoachAvailability, id=slot_id, coach=request.user)
    if slot.is_booked:
        return JsonResponse({'error': 'Cannot edit a booked slot'}, status=400)
    data = json.loads(request.body)
    start_str = data.get('start_time')
    end_str = data.get('end_time')
    if not start_str or not end_str:
        return JsonResponse({'error': 'Missing times'}, status=400)
    try:
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt)
        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt)
    except ValueError:
        return JsonResponse({'error': 'Invalid datetime'}, status=400)
    if start_dt < timezone.now():
        return JsonResponse({'error': 'Cannot set slot in the past'}, status=400)
    if (end_dt - start_dt) != timedelta(hours=1):
        return JsonResponse({'error': 'Slot must be exactly one hour'}, status=400)
    weekday = start_dt.weekday()
    try:
        gym = GymInfo.objects.get(day=weekday)
        if not gym.is_open:
            return JsonResponse({'error': 'Gym closed on this day'}, status=400)
        if start_dt.time() < gym.open_time or end_dt.time() > gym.close_time:
            return JsonResponse({'error': 'Slot outside gym hours'}, status=400)
    except GymInfo.DoesNotExist:
        return JsonResponse({'error': 'Gym hours not configured'}, status=400)
    overlapping = CoachAvailability.objects.filter(
        coach=request.user,
        start_time__lt=end_dt,
        end_time__gt=start_dt,
        is_booked=False
    ).exclude(pk=slot.pk)
    if overlapping.exists():
        return JsonResponse({'error': 'Overlaps with existing availability'}, status=400)
    slot.start_time = start_dt
    slot.end_time = end_dt
    slot.save()
    return JsonResponse({'id': slot.id, 'start': slot.start_time.isoformat(), 'end': slot.end_time.isoformat()})

@login_required(login_url='login')
@user_passes_test(is_coach)
def ajax_delete_availability(request, slot_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    slot = get_object_or_404(CoachAvailability, id=slot_id, coach=request.user)
    if slot.is_booked:
        return JsonResponse({'error': 'Cannot delete a booked slot'}, status=400)
    slot.delete()
    return JsonResponse({'deleted': slot_id})

@login_required(login_url='login')
@user_passes_test(is_coach)
def ajax_cancel_series(request, group_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    slots = CoachAvailability.objects.filter(
        coach=request.user,
        recurrence_group=group_id,
        start_time__gte=timezone.now(),
        is_booked=False
    )
    count = slots.count()
    slots.delete()
    return JsonResponse({'deleted_count': count})

@login_required
def api_coaches(request):
    coaches = CustomUser.objects.filter(role='COACH', is_active=True).values('id', 'first_name', 'last_name')
    return JsonResponse(list(coaches), safe=False)

@login_required
def api_coach_availability(request):
    coach_id = request.GET.get('coach_id')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    if not coach_id or not start_date or not end_date:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    try:
        coach = CustomUser.objects.get(id=coach_id, role='COACH')
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Coach not found'}, status=404)
    start_utc, _ = local_date_to_utc_range(start_date)
    _, end_utc = local_date_to_utc_range(end_date)
    slots = CoachAvailability.objects.filter(
        coach=coach,
        start_time__gte=start_utc,
        start_time__lt=end_utc,
        is_booked=False
    ).order_by('start_time').values('id', 'start_time', 'end_time')
    slot_list = [{'id': slot['id'], 'start_time': slot['start_time'].isoformat(), 'end_time': slot['end_time'].isoformat()} for slot in slots]
    return JsonResponse(slot_list, safe=False)

@login_required
def api_all_availability(request):
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Missing date'}, status=400)
    start_utc, end_utc = local_date_to_utc_range(date_str)
    slots = CoachAvailability.objects.filter(
        start_time__gte=start_utc,
        start_time__lt=end_utc,
        is_booked=False
    ).select_related('coach').order_by('start_time')
    data = [
        {
            'id': slot.id,
            'coach_id': slot.coach.id,
            'coach_name': f"{slot.coach.first_name} {slot.coach.last_name}",
            'start_time': slot.start_time.isoformat(),
            'end_time': slot.end_time.isoformat(),
        }
        for slot in slots
    ]
    return JsonResponse(data, safe=False)

@login_required
@require_POST
@ensure_csrf_cookie
def api_request_appointment(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    coach_id = data.get('coach_id')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    if not coach_id or not start_time_str or not end_time_str:
        return JsonResponse({'error': 'Missing fields'}, status=400)
    try:
        start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt)
        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt)
    except ValueError:
        return JsonResponse({'error': 'Invalid datetime format'}, status=400)
    try:
        availability = CoachAvailability.objects.get(
            coach_id=coach_id,
            start_time=start_dt,
            end_time=end_dt,
            is_booked=False
        )
    except CoachAvailability.DoesNotExist:
        return JsonResponse({'error': 'This time slot is no longer available'}, status=400)
    appointment = CoachAppointment.objects.create(
        coach_id=coach_id,
        member=request.user,
        start_time=start_dt,
        end_time=end_dt,
        status='PENDING',
        availability=availability
    )
    availability.is_booked = True
    availability.save()
    return JsonResponse({'success': True, 'appointment_id': appointment.id})

@login_required(login_url='login')
@user_passes_test(is_coach)
@require_POST
def ajax_accept_appointment(request, appointment_id):
    appointment = get_object_or_404(CoachAppointment, id=appointment_id, coach=request.user, status='PENDING')
    appointment.status = 'ACCEPTED'
    appointment.save()
    return JsonResponse({'success': True})

@login_required(login_url='login')
@require_POST
def ajax_cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(CoachAppointment, id=appointment_id, member=request.user)
    if appointment.status not in ['PENDING', 'ACCEPTED']:
        return JsonResponse({'error': 'This appointment cannot be cancelled.'}, status=400)
    appointment.status = 'CANCELLED'
    appointment.save()
    if appointment.availability:
        appointment.availability.is_booked = False
        appointment.availability.save()
    return JsonResponse({'success': True})

@login_required(login_url='login')
@user_passes_test(is_coach)
@require_POST
def ajax_reject_appointment(request, appointment_id):
    appointment = get_object_or_404(CoachAppointment, id=appointment_id, coach=request.user, status='PENDING')
    appointment.status = 'REFUSED'
    appointment.save()
    return JsonResponse({'success': True})

@login_required(login_url='login')
@user_passes_test(is_member)
def api_coach_search(request):
    query = request.GET.get('q', '')
    coaches = CustomUser.objects.filter(
        role='COACH', is_active=True
    ).filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
    ).values('id', 'first_name', 'last_name', 'email')[:20]
    return JsonResponse(list(coaches), safe=False)

@login_required(login_url='login')
def send_message(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    recipient_id = request.POST.get('recipient_id')
    subject = request.POST.get('subject')
    body = request.POST.get('body')
    if not recipient_id or not subject or not body:
        messages.error(request, 'All fields are required.')
        return redirect('user_inbox')
    try:
        recipient = CustomUser.objects.get(id=recipient_id, role='COACH')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid recipient.')
        return redirect('user_inbox')
    Message.objects.create(sender=request.user, recipient=recipient, subject=subject, body=body)
    messages.success(request, 'Message sent.')
    return redirect('user_inbox')

@login_required(login_url='login')
def reply_message(request, message_id):
    original = get_object_or_404(Message, id=message_id, recipient=request.user)
    if request.method == 'POST':
        body = request.POST.get('body')
        if not body:
            messages.error(request, 'Message body cannot be empty.')
            return redirect('user_inbox')
        Message.objects.create(
            sender=request.user,
            recipient=original.sender,
            subject=f"Re: {original.subject}",
            body=body
        )
        messages.success(request, 'Reply sent.')
        return redirect('user_inbox')
    else:
        return render(request, 'CUFitness/user/user_coach_reply.html', {'original': original})

@login_required(login_url='login')
def mark_read(request, message_id):
    if request.method == 'POST':
        msg = get_object_or_404(Message, id=message_id, recipient=request.user)
        msg.is_read = True
        msg.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Method not allowed'}, status=405)
# endregion
# endregion

# =================================================================================================================
# ============Potentially Not used Functions===========
# (All legacy/commented code remains below as in your original file)
# @login_required(login_url='login')
# @user_passes_test(is_coach)
# def manage_availability(request):
#     """Add/delete availability slots."""
#     if request.method == 'POST':
#         form = CoachAvailabilityForm(request.POST)
#         if form.is_valid():
#             availability = form.save(commit=False)
#             availability.coach = request.user
#             availability.save()
#             messages.success(request, 'Availability slot added.')
#             return redirect('manage_availability')
#     else:
#         form = CoachAvailabilityForm()
#     slots = CoachAvailability.objects.filter(coach=request.user).order_by('start_time')
#     context = {
#         'form': form,
#         'slots': slots,
#     }
#
#     # TODO New url needed
#
#     return render(request, 'CUFitness/manage_availability.html', context)

# @login_required(login_url='login')
# @user_passes_test(is_coach)
# def manage_appointments(request):
#     # View pending appointments and respond
#     pending = (CoachAppointment.objects.filter
#                (coach=request.user,
#                 status='PENDING'
#                 ).order_by('start_time')).select_related(
#         'member')  # Without (select_related('member')), accessing appointment.member.first_name in the template triggers an extra query per row (N+1).
#
#     if request.method == 'POST':
#         appointment_id = request.POST.get('appointment_id')
#
#         try:
#             with transaction.atomic():
#                 # lock this row until the request completes
#                 appointment = CoachAppointment.objects.select_for_update().get(
#                     id=appointment_id,
#                     coach=request.user
#                 )
#                 form = AppointmentResponseForm(request.POST, instance=appointment)
#                 if form.is_valid():
#                     form.save()  # clean() runs here, safely locked
#                     messages.success(request, f'Appointment {appointment.status}.')
#                     return redirect('manage_appointments')
#         except CoachAppointment.DoesNotExist:
#             messages.error(request, 'Appointment not found.')
#             return redirect('manage_appointments')
#
#     else:
#         form = AppointmentResponseForm()
#
#     context = {
#         'pending_appointments': pending,
#         'response_form': form,
#     }
#     return render(request, 'CUFitness/manage_appointments.html', context)

# --- Member Views ---
#
# '''
# # not needed anymore... coach list is displayed in home page
# @login_required(login_url='login')
# @user_passes_test(is_member)
# def coach_list_view(request):
#     coaches = CustomUser.objects.filter(role='COACH', is_active=True)
#
#     # TODO need a html page to display the list of coach. change url if necessary
#     return render(request, 'CUFitness/coach_list.html', {'coaches': coaches})
#
# '''
#
# class CoachAvailabilityViewSet(viewsets.ModelViewSet):
#     """
#     Manage availability slots. Coaches can CRUD their own; members can only read unbooked slots.
#     """
#     queryset = CoachAvailability.objects.all()
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['is_booked', 'start_time', 'end_time', 'coach']
#
#     def get_queryset(self):
#         user = self.request.user
#         if not user.is_authenticated:
#             return CoachAvailability.objects.none()
#         if is_coach(user):
#             return CoachAvailability.objects.filter(coach=user)
#         # Members can see all unbooked slots
#         return CoachAvailability.objects.filter(is_booked=False)
#
#     def perform_create(self, serializer):
#         if not is_coach(self.request.user):
#             raise PermissionError("Only coaches can create availability slots.")
#         serializer.save(coach=self.request.user)
#
#     def perform_update(self, serializer):
#         slot = self.get_object()
#         if slot.is_booked:
#             raise PermissionError("Cannot edit a booked slot.")
#         serializer.save()
#
#     def perform_destroy(self, instance):
#         if instance.is_booked:
#             raise PermissionError("Cannot delete a booked slot.")
#         instance.delete()
#
#
# class CoachAppointmentViewSet(viewsets.ModelViewSet):
#     """
#     Appointments between members and coaches.
#     """
#     queryset = CoachAppointment.objects.all()
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['status', 'coach', 'member', 'start_time', 'end_time']
#
#     def get_queryset(self):
#         user = self.request.user
#         if is_coach(user):
#             return CoachAppointment.objects.filter(coach=user)
#         elif is_member(user):
#             return CoachAppointment.objects.filter(member=user)
#         elif is_staff_user(user):
#             return CoachAppointment.objects.all()
#         return CoachAppointment.objects.none()
#
#     @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
#     def accept(self, request, pk=None):
#         """Coach accepts a pending appointment."""
#         appointment = self.get_object()
#         if appointment.coach != request.user:
#             return Response({'detail': 'Not your appointment.'}, status=status.HTTP_403_FORBIDDEN)
#         if appointment.status != 'PENDING':
#             return Response({'detail': 'Appointment is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
#         appointment.status = 'ACCEPTED'
#         appointment.save()
#         return Response({'status': 'accepted'})
#
#     @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
#     def reject(self, request, pk=None):
#         """Coach rejects a pending appointment, optionally with a reason."""
#         appointment = self.get_object()
#         if appointment.coach != request.user:
#             return Response({'detail': 'Not your appointment.'}, status=status.HTTP_403_FORBIDDEN)
#         if appointment.status != 'PENDING':
#             return Response({'detail': 'Appointment is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
#         reason = request.data.get('refusal_reason', '')
#         appointment.status = 'REFUSED'
#         appointment.refusal_reason = reason
#         appointment.save()
#         return Response({'status': 'rejected'})
#
#     @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
#     def cancel(self, request, pk=None):
#         """Member cancels an appointment."""
#         appointment = self.get_object()
#         if appointment.member != request.user:
#             return Response({'detail': 'Not your appointment.'}, status=status.HTTP_403_FORBIDDEN)
#         if appointment.status not in ['PENDING', 'ACCEPTED']:
#             return Response({'detail': 'Cannot cancel this appointment.'}, status=status.HTTP_400_BAD_REQUEST)
#         appointment.status = 'CANCELLED'
#         appointment.save()
#         return Response({'status': 'cancelled'})
#
#
# class ArticleViewSet(viewsets.ModelViewSet):
#     """
#     Articles. Staff can create/update/delete; members can read.
#     """
#     queryset = Article.objects.all()
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     filter_backends = [SearchFilter]
#     search_fields = ['title', 'description', 'body']
#
#     def get_queryset(self):
#         # If not logged in, only free articles
#         if not self.request.user.is_authenticated:
#             return Article.objects.filter(locked=False)
#         return Article.objects.all()
#
#     def perform_create(self, serializer):
#         serializer.save(author=self.request.user)
#
#     def perform_update(self, serializer):
#         # Staff only? Check role
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can edit articles.")
#         serializer.save()
#
#     def perform_destroy(self, instance):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can delete articles.")
#         instance.delete()
#
#
# class RecipeViewSet(viewsets.ModelViewSet):
#     """
#     Recipes. Staff can create/update/delete; members can read.
#     """
#     queryset = Recipe.objects.all()
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     filter_backends = [SearchFilter]
#     search_fields = ['title', 'description', 'instructions']
#
#     def get_queryset(self):
#         if not self.request.user.is_authenticated:
#             return Recipe.objects.filter(locked=False)
#         return Recipe.objects.all()
#
#     def perform_create(self, serializer):
#         serializer.save(author=self.request.user)
#
#     def perform_update(self, serializer):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can edit recipes.")
#         serializer.save()
#
#     def perform_destroy(self, instance):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can delete recipes.")
#         instance.delete()
#
#
# class WorkoutPlanViewSet(viewsets.ModelViewSet):
#     """
#     Workout plans. Staff can create/update/delete; members can read.
#     """
#     queryset = WorkoutPlan.objects.all()
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     filter_backends = [SearchFilter]
#     search_fields = ['title', 'description', 'body']
#
#     def get_queryset(self):
#         if not self.request.user.is_authenticated:
#             return WorkoutPlan.objects.filter(locked=False)
#         return WorkoutPlan.objects.all()
#
#     def perform_create(self, serializer):
#         serializer.save(author=self.request.user)
#
#     def perform_update(self, serializer):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can edit workouts.")
#         serializer.save()
#
#     def perform_destroy(self, instance):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can delete workouts.")
#         instance.delete()
#
#
# class ExerciseViewSet(viewsets.ModelViewSet):
#     """
#     Exercises. Staff can create/update/delete; members can read.
#     """
#     queryset = Exercise.objects.all()
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     filter_backends = [SearchFilter, OrderingFilter]
#     search_fields = ['title', 'description', 'instructions']
#     ordering_fields = ['created_at', 'title']
#
#     def perform_create(self, serializer):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can create exercises.")
#         serializer.save(created_by=self.request.user)
#
#     def perform_update(self, serializer):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can edit exercises.")
#         serializer.save()
#
#     def perform_destroy(self, instance):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can delete exercises.")
#         instance.delete()
#
#
# class MessageViewSet(viewsets.ModelViewSet):
#     """
#     Messages between members and coaches.
#     """
#     queryset = Message.objects.all()
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['recipient', 'is_read']
#
#     def get_queryset(self):
#         user = self.request.user
#         # Users see messages they sent or received
#         return Message.objects.filter(
#             Q(sender=user) | Q(recipient=user)
#         ).order_by('-timestamp')
#
#     def perform_create(self, serializer):
#         # Only members can send messages (to coaches)
#         if not is_member(self.request.user):
#             raise PermissionError("Only members can send messages.")
#         # Ensure recipient is a coach
#         recipient = serializer.validated_data.get('recipient')
#         if recipient.role != 'COACH':
#             raise PermissionError("Messages can only be sent to coaches.")
#         serializer.save(sender=self.request.user)
#
#     @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
#     def mark_read(self, request, pk=None):
#         """Mark a received message as read."""
#         message = self.get_object()
#         if message.recipient != request.user:
#             return Response({'detail': 'Not your message.'}, status=status.HTTP_403_FORBIDDEN)
#         message.is_read = True
#         message.save()
#         return Response({'status': 'read'})
#
#
# class ChallengeViewSet(viewsets.ModelViewSet):
#     """
#     Fitness challenges.
#     """
#     queryset = Challenge.objects.all()
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     filter_backends = [SearchFilter, OrderingFilter]
#     search_fields = ['title', 'description']
#     ordering_fields = ['start_date', 'end_date', 'created_at']
#
#     def perform_create(self, serializer):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can create challenges.")
#         serializer.save(created_by=self.request.user)
#
#     def perform_update(self, serializer):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can edit challenges.")
#         serializer.save()
#
#     def perform_destroy(self, instance):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can delete challenges.")
#         instance.delete()
#
#
# class ChallengeParticipationViewSet(viewsets.ModelViewSet):
#     """
#     User participation in challenges.
#     """
#     queryset = ChallengeParticipation.objects.all()
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['challenge']
#
#     def get_queryset(self):
#         user = self.request.user
#         # Users see their own participation; staff see all
#         if is_staff_user(user):
#             return ChallengeParticipation.objects.all()
#         return ChallengeParticipation.objects.filter(user=user)
#
#     def perform_create(self, serializer):
#         # Ensure user is authenticated and not already participating
#         challenge = serializer.validated_data.get('challenge')
#         if ChallengeParticipation.objects.filter(user=self.request.user, challenge=challenge).exists():
#             raise PermissionError("Already participating in this challenge.")
#         serializer.save(user=self.request.user)
#
#     @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
#     def update_progress(self, request, pk=None):
#         """Increment progress for a participation."""
#         participation = self.get_object()
#         if participation.user != request.user:
#             return Response({'detail': 'Not your participation.'}, status=status.HTTP_403_FORBIDDEN)
#         increment = request.data.get('progress', 0)
#         try:
#             increment = int(increment)
#         except ValueError:
#             return Response({'detail': 'Invalid progress value.'}, status=status.HTTP_400_BAD_REQUEST)
#         participation.progress += increment
#         # Cap at goal
#         if participation.progress > participation.challenge.goal_target:
#             participation.progress = participation.challenge.goal_target
#         participation.save()
#         return Response({'progress': participation.progress, 'percentage': participation.progress_percentage()})
#
#
# class GymInfoViewSet(viewsets.ModelViewSet):
#     """
#     Gym operating hours. Staff can edit; members can view.
#     """
#     queryset = GymInfo.objects.all()
#     permission_classes = [IsAuthenticatedOrReadOnly]
#
#     def perform_create(self, serializer):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can manage gym info.")
#         serializer.save()
#
#     def perform_update(self, serializer):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can manage gym info.")
#         serializer.save()
#
#     def perform_destroy(self, instance):
#         if not is_staff_user(self.request.user):
#             raise PermissionError("Only staff can manage gym info.")
#         instance.delete()