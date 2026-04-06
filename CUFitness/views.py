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
from rest_framework.exceptions import PermissionDenied, ValidationError as DRFValidationError

# Local import
from .forms import (
    ArticleForm, ChallengeForm, ContactMessageForm, CustomUserCreationForm,
    ExerciseForm, IngredientFormSet, PrivacySettingsForm, ProfilePictureForm,
    RecipeForm, UpdateEmailForm, UpdatePasswordForm, ChallengeForm, WorkoutPlanForm,
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

def login_required_any_role(view_func):
    """
    Blocks anonymous users only. Any authenticated role (MEMBER, COACH, STAFF, ADMIN)
    is allowed through. Anonymous users are redirected to the member login page.
    Use this instead of @login_required on views that are role-agnostic.
    """
    return login_required(view_func, login_url='login')



# =================================================================================================================
# ============================================== FUNCTIONALITY ====================================================
# =================================================================================================================

# region ----------- General Website Navigation -----------
def home(request):
    if request.user.is_authenticated and request.user.role == 'STAFF':
        active_members = CustomUser.objects.filter(role="MEMBER", is_active=True).order_by("first_name")
        active_coaches = CustomUser.objects.filter(role="COACH", is_active=True).order_by("first_name")
        return render(request, "CUFitness/staff/staff_home.html",
                      {"active_members": active_members, "active_coaches": active_coaches})
    elif request.user.is_authenticated and request.user.role == 'COACH':
        return redirect('coach_home')
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

# region -----------   Resources-Dropdown Pages  -----------
def user_articles(request):
    free_articles = Article.objects.filter(locked=False)
    locked_articles = Article.objects.filter(locked=True)
    return render(request, 'CUFitness/general_website/navbar/articles.html',
                  {"free_articles": free_articles, "locked_articles": locked_articles})

def user_recipes(request):

    free_recipes = Recipe.objects.filter(locked=False)
    locked_recipes = Recipe.objects.filter(locked=True)

    return render(request, "CUFitness/general_website/navbar/recipes.html",
                  {"free_recipes": free_recipes, "locked_recipes": locked_recipes,})

def workout_plans(request):
    free_workouts = WorkoutPlan.objects.filter(locked=False).prefetch_related('exercises')
    locked_workouts = WorkoutPlan.objects.filter(locked=True).prefetch_related('exercises')
    return render(request, 'CUFitness/general_website/navbar/workout_plans.html', {
        'free_workouts': free_workouts,
        'locked_workouts': locked_workouts,
    })

def user_exercises(request):
    exercises = Exercise.objects.all().order_by('muscle_group')
    return render(request, "CUFitness/general_website/navbar/exercises.html", {"exercises": exercises})

def user_challenges(request):
    if request.user.is_authenticated:
        challenges = Challenge.objects.all()
        user_participation = ChallengeParticipation.objects.filter(user=request.user)
        joined_ids = user_participation.values_list('challenge_id', flat=True)
        leaderboard_data = []
        for challenge in challenges:
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

# region ----------- More-Tab Dropdown Pages -----------
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

# endregion

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
        if user is not None and user.role == 'MEMBER':
            login(request, user)
            messages.success(request, 'You have been logged in as ' + user.first_name)
            return redirect('home')
        elif user is not None and user.role == 'STAFF':
            messages.error(request, 'Staff members go to staff login')
            return redirect('staff_login')
        elif user is not None and user.role == 'COACH':
            messages.error(request, 'Coaches go to coach login')
            return redirect('coach_login')
        else:
            messages.error(request, 'Invalid Account Email or Password')
            return redirect('login')
    else:
        return render(request, 'CUFitness/general_website/authentication/login.html')

def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('home')

# endregion

# region ----------- Logged-In User Views  -----------
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
    if request.user.is_authenticated and request.user.role == 'COACH':
        return redirect('coach_settings')
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
    user = request.user
    # Get messages where user is sender or recipient
    message_list = Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).select_related('sender', 'recipient').order_by('-timestamp')

    if is_member(user):
        coaches = CustomUser.objects.filter(role='COACH', is_active=True).order_by('first_name')
        context = {
            'message_list': message_list,
            'coaches': coaches,
            'is_member': True,
        }
    else:
        context = {
            'message_list': message_list,
            'is_member': False,
        }
    return render(request, 'CUFitness/user/user_inbox.html', context)

@login_required(login_url='login')
def user_calendar(request):
    if is_coach(request.user):
        return redirect('coach_schedule')

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

    # Add refused appointments (any time)
    rejected_appointments = CoachAppointment.objects.filter(
        member=request.user,
        status='REFUSED'
    ).select_related('coach').order_by('-start_time')[:10]

    for appt in past_appointments:
        appt.can_review = (appt.status == 'ACCEPTED' and not hasattr(appt, 'review'))
        appt.has_review = hasattr(appt, 'review')
    for appt in rejected_appointments:
        appt.can_review = not hasattr(appt, 'review')
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
        'rejected_appointments': rejected_appointments,
        'calendar_events_json': json.dumps(calendar_events),
        'is_coach': False,
    }
    return render(request, 'CUFitness/user/user_calendar.html', context)

# endregion

# region ----------- Coach Views -----------

def coach_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None and user.role == 'COACH':
            login(request, user)
            messages.success(request, 'You have been logged in as ' + user.first_name)
            return redirect('coach_home')
        else:
            messages.error(request, 'Invalid Account Email or Password')
            return redirect('coach_login')
    else:
        return render(request, 'CUFitness/coach/coach_login.html')

@login_required(login_url='login')
@user_passes_test(is_coach)
def coach_home(request):
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
    return render(request, 'CUFitness/coach/coach_home.html', context)

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

@login_required(login_url='login')
@user_passes_test(is_coach)
def coach_schedule(request):
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
            if g.is_open and g.is_open_24h:
                open_time_str = "00:00"
                close_time_str = "24:00"
            else:
                open_time_str = g.open_time.isoformat() if g.open_time else None
                close_time_str = g.close_time.isoformat() if g.close_time else None
            gym_info[day.isoformat()] = {
                'is_open': g.is_open,
                'open_time': open_time_str,
                'close_time': close_time_str,
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
    return render(request, 'CUFitness/coach/coach_schedule.html', context)

@login_required(login_url='coach_login')
@user_passes_test(is_coach)
def coach_settings(request):
    email_form = UpdateEmailForm(instance=request.user)
    password_form = UpdatePasswordForm(user=request.user)
    if request.method == 'POST':
        if 'email_submit' in request.POST:
            email_form = UpdateEmailForm(request.POST, instance=request.user)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, 'Email address updated.')
                return redirect('coach_settings')
        elif 'password_submit' in request.POST:
            password_form = UpdatePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password updated successfully.')
                return redirect('coach_settings')
    context = {
        'email_form': email_form,
        'password_form': password_form,
    }
    return render(request, 'CUFitness/coach/coach_settings.html', context)

# endregion

# region ----------- Staff Views -----------

# region -----------  Staff General navigation  -----------
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
        return redirect('staff_messages')
    return render(request, 'CUFitness/staff/staff_messages.html', {'messages': all_messages})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_user_details(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    return render(request, "CUFitness/staff/staff_user_details.html", {"user_obj": user_obj})
# endregion

# region -----------  Article Pages  -----------
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

 # -----------  Staff Article Pages  -----------
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


@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_edit_article(request, id):
    article = get_object_or_404(Article, id=id)
    # Allow any staff to edit if the original author's account has been deleted (author=None)
    if article.author is not None and request.user != article.author:
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
    if article.author is not None and request.user != article.author:
        messages.error(request, 'You do not have permission to delete this article.')
        return redirect('staff_articles')
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted successfully.')
        return redirect('staff_articles')
    return HttpResponseNotAllowed(['POST'])
# endregion

# region -----------  Recipe Pages  -----------
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

# -----------  Staff Recipe Pages  -----------
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
    if recipe.author is not None and request.user != recipe.author:
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
    if recipe.author is not None and request.user != recipe.author:
        messages.error(request, 'You do not have permission to delete this recipe.')
        return redirect('staff_recipes')
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe deleted successfully.')
        return redirect('staff_recipes')
    return HttpResponseNotAllowed(['POST'])
# endregion

# region -----------  Workout Pages  -----------
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

# -----------  Staff Workout Pages  -----------
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_workouts(request):
    all_workout_plans = WorkoutPlan.objects.all()
    return render(request, 'CUFitness/staff/workout_plans/staff_workouts.html', {'workout_plans': all_workout_plans})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_create_workout(request):
    if request.method == 'POST':
        form = WorkoutPlanForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)
            workout.author = request.user
            workout.save()
            messages.success(request, 'Workout plan created successfully.')
            return redirect('staff_workouts')
    else:
        form = WorkoutPlanForm()
    return render(request, 'CUFitness/staff/workout_plans/staff_create_workout.html', {'form': form})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_edit_workout(request, id):
    workout = get_object_or_404(WorkoutPlan, id=id)
    if workout.author is not None and request.user != workout.author:
        messages.error(request, 'You do not have permission to edit this workout plan.')
        return redirect('staff_workouts')
    if request.method == 'POST':
        form = WorkoutPlanForm(request.POST, instance=workout)
        if form.is_valid():
            form.save()
            messages.success(request, 'Workout plan updated successfully.')
            return redirect('workout_plan_details', id=workout.id)
    else:
        form = WorkoutPlanForm(instance=workout)
    return render(request, 'CUFitness/staff/workout_plans/staff_edit_workout.html', {'form': form, 'workout': workout})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_delete_workout(request, id):
    workout = get_object_or_404(WorkoutPlan, id=id)
    if workout.author is not None and request.user != workout.author:
        messages.error(request, 'You do not have permission to delete this workout plan.')
        return redirect('staff_workouts')
    if request.method == 'POST':
        workout.delete()
        messages.success(request, 'Workout plan deleted successfully.')
        return redirect('staff_workouts')
    return HttpResponseNotAllowed(['POST'])
# endregion

# region -----------  Exercise Pages  -----------
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

# -----------  Staff Exercise Pages  -----------
@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_exercises(request):
    exercises = Exercise.objects.all().order_by('muscle_group')
    return render(request, 'CUFitness/staff/exercises/staff_exercises.html', {'exercises': exercises})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_create_exercise(request):
    if request.method == 'POST':
        form = ExerciseForm(request.POST)
        if form.is_valid():
            exercise = form.save(commit=False)
            exercise.created_by = request.user
            exercise.save()
            messages.success(request, 'Exercise created successfully.')
            return redirect('staff_exercises')
    else:
        form = ExerciseForm()
    return render(request, 'CUFitness/staff/exercises/staff_create_exercise.html', {'form': form})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_edit_exercise(request, id):
    exercise = get_object_or_404(Exercise, id=id)
    if request.method == 'POST':
        form = ExerciseForm(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exercise updated successfully.')
            return redirect('exercise_details', id=exercise.id)
    else:
        form = ExerciseForm(instance=exercise)
    return render(request, 'CUFitness/staff/exercises/staff_edit_exercise.html', {'form': form, 'exercise': exercise})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_delete_exercise(request, id):
    exercise = get_object_or_404(Exercise, id=id)
    if request.method == 'POST':
        exercise.delete()
        messages.success(request, 'Exercise deleted successfully.')
        return redirect('staff_exercises')
    return HttpResponseNotAllowed(['POST'])
# endregion

# region  -----------  Challenge Pages  -----------

@login_required_any_role
def challenge_details(request, id):
    challenge = get_object_or_404(Challenge, id=id)
    base = 'CUFitness/staff/staff_base.html' if request.user.role in ('STAFF', 'ADMIN') else 'CUFitness/general_website/base.html'
    participants = ChallengeParticipation.objects.filter(challenge=challenge).select_related('user').order_by('-progress')
    is_joined = ChallengeParticipation.objects.filter(user=request.user, challenge=challenge).exists()
    return render(request, 'CUFitness/staff/challenges/challenge_details.html', {
        'challenge': challenge,
        'participants': participants,
        'base_template': base,
        'is_joined': is_joined,
    })

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_challenges(request):
    challenges = Challenge.objects.all()
    return render(request, 'CUFitness/staff/challenges/staff_challenges.html', {'challenges': challenges})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_create_challenge(request):
    if request.method == "POST":
        form = ChallengeForm(request.POST)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.created_by = request.user
            challenge.save()
            return redirect('staff_challenges')
    else:
        form = ChallengeForm()
    return render(request, 'CUFitness/staff/challenges/staff_create_challenge.html', {'form': form})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_edit_challenge(request, id):
    challenge = get_object_or_404(Challenge, id=id)
    if request.method == 'POST':
        form = ChallengeForm(request.POST, instance=challenge)
        if form.is_valid():
            form.save()
            messages.success(request, 'Challenge updated successfully.')
            return redirect('challenge_details', id=challenge.id)
    else:
        form = ChallengeForm(instance=challenge)
    return render(request, 'CUFitness/staff/challenges/staff_edit_challenge.html', {'form': form, 'challenge': challenge})

@login_required(login_url='staff_login')
@user_passes_test(is_staff_user)
def staff_delete_challenge(request, id):
    challenge = get_object_or_404(Challenge, id=id)
    if request.method == 'POST':
        challenge.delete()
        messages.success(request, 'Challenge deleted successfully.')
        return redirect('staff_challenges')
    return HttpResponseNotAllowed(['POST'])

# -----------  System Challenges Pages  -----------
@login_required(login_url='login')
def join_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    ChallengeParticipation.objects.get_or_create(user=request.user, challenge=challenge)
    return redirect('user_challenges')

@login_required(login_url='login')
def update_progress(request, participation_id):
    participation = get_object_or_404(ChallengeParticipation, id=participation_id, user=request.user)
    if request.method == "POST":
        try:
            increment = int(request.POST.get('progress', 0))
        except (ValueError, TypeError):
            increment = 0
        # Clamp increment to a non-negative value — negative submissions would silently
        # decrease progress, which is never a valid user action.
        increment = max(0, increment)
        participation.progress = min(
            participation.progress + increment,
            participation.challenge.goal_target
        )
        participation.save()
        participation.refresh_from_db()
    return redirect('user_challenges')

# endregion

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
            raise PermissionDenied("Only members can write reviews.")
        appointment_id = self.request.data.get('appointment')
        if not appointment_id:
            raise DRFValidationError("Appointment ID is required.")
        try:
            appointment = CoachAppointment.objects.get(id=appointment_id)
        except CoachAppointment.DoesNotExist:
            raise DRFValidationError("Appointment not found.")
        if appointment.member != user:
            raise PermissionDenied("You can only review your own appointments.")
        # Allow review for ACCEPTED or REFUSED appointments (for testing)
        if appointment.status not in ['ACCEPTED', 'REFUSED']:
            raise DRFValidationError("You can only review accepted or refused appointments.")
        if hasattr(appointment, 'review'):
            raise DRFValidationError("This appointment has already been reviewed.")
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
        max_weeks = 52 # max one year
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
        # Skip time check for 24h days
        if not gym.is_open_24h:
            if local_start.time() < gym.open_time or local_end.time() > gym.close_time:
                return JsonResponse({'error': f'Slot {local_start.time()} outside gym hours'}, status=400)
        if recurrence == 'none':
            overlapping = CoachAvailability.objects.filter(
                coach=request.user,
                start_time__lt=end_dt,
                end_time__gt=start_dt,
                #is_booked=False
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
                    #is_booked=False
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
@ensure_csrf_cookie
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
    local_start = to_local_time(start_dt)
    local_end = to_local_time(end_dt)
    weekday = local_start.weekday()
    try:
        gym = GymInfo.objects.get(day=weekday)
        if not gym.is_open:
            return JsonResponse({'error': 'Gym closed on this day'}, status=400)
        if not gym.is_open_24h:
            if gym.open_time is None or gym.close_time is None:
                return JsonResponse({'error': 'Gym hours not set for this day'}, status=400)
            if local_start.time() < gym.open_time or local_end.time() > gym.close_time:
                return JsonResponse({'error': 'Slot outside gym hours'}, status=400)
    except GymInfo.DoesNotExist:
        return JsonResponse({'error': 'Gym hours not configured'}, status=400)
    overlapping = CoachAvailability.objects.filter(
        coach=request.user,
        start_time__lt=end_dt,
        end_time__gt=start_dt,
    ).exclude(pk=slot.pk)
    if overlapping.exists():
        return JsonResponse({'error': 'Overlaps with an existing slot'}, status=400)
    slot.start_time = start_dt
    slot.end_time = end_dt
    try:
        slot.save()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'id': slot.id, 'start': slot.start_time.isoformat(), 'end': slot.end_time.isoformat()})

@login_required(login_url='login')
@user_passes_test(is_coach)
@ensure_csrf_cookie
def ajax_delete_availability(request, slot_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    slot = get_object_or_404(CoachAvailability, id=slot_id, coach=request.user)
    if slot.is_booked:
        return JsonResponse({'error': 'Cannot delete a booked slot'}, status=400)
    try:
        slot.delete()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
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

    # Atomic block + select_for_update ensures only one request can book this slot
    # at a time — concurrent requests will queue and the second will see is_booked=True
    try:
        with transaction.atomic():
            try:
                availability = CoachAvailability.objects.select_for_update().get(
                    coach_id=coach_id,
                    start_time=start_dt,
                    end_time=end_dt,
                    is_booked=False
                )
            except CoachAvailability.DoesNotExist:
                return JsonResponse({'error': 'This time slot is no longer available'}, status=400)

            # Double-check that there is no active appointment for this slot (optional safety)
            if CoachAppointment.objects.filter(availability=availability, status__in=['PENDING', 'ACCEPTED']).exists():
                return JsonResponse({'error': 'This slot is already booked or pending'}, status=400)

            # Create the appointment and mark the slot booked atomically
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
    except Exception as e:
        return JsonResponse({'error': 'Booking failed, please try again.'}, status=500)

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
    """Cancel a pending appointment (member only)."""
    try:
        appointment = CoachAppointment.objects.get(id=appointment_id, member=request.user)
    except CoachAppointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found.'}, status=404)

    if appointment.status not in ['PENDING', 'ACCEPTED']:
        return JsonResponse({'error': 'This appointment cannot be cancelled.'}, status=400)

    # Free the linked availability slot BEFORE changing appointment status
    if appointment.availability:
        availability = appointment.availability
        availability.is_booked = False
        availability.save()
        # Remove the link to avoid any future confusion
        appointment.availability = None

    appointment.status = 'CANCELLED'
    appointment.save()

    return JsonResponse({'success': True})

@login_required(login_url='login')
@user_passes_test(is_coach)
@require_POST
def ajax_reject_appointment(request, appointment_id):
    appointment = get_object_or_404(CoachAppointment, id=appointment_id, coach=request.user, status='PENDING')
    try:
        data = json.loads(request.body)
        reason = data.get('refusal_reason', '').strip()
    except json.JSONDecodeError:
        reason = ''
    if not reason:
        return JsonResponse({'error': 'Refusal reason is required.'}, status=400)
    if len(reason) > 500:
        return JsonResponse({'error': 'Reason must be 500 characters or less.'}, status=400)
    appointment.status = 'REFUSED'
    appointment.refusal_reason = reason
    appointment.save()
    # Free the linked availability slot so it can be booked again
    if appointment.availability:
        availability = appointment.availability
        availability.is_booked = False
        availability.save()
        appointment.availability = None
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