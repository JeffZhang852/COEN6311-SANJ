from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.http import HttpResponseNotAllowed
from django.contrib.auth.decorators import permission_required, user_passes_test, login_required
from django.contrib import messages

from .models import CustomUser, CoachAppointment, CoachAvailability, EquipmentList, Article, Recipe, RecipeIngredient, GymInfo, Exercise
from .forms import CoachRequestForm, CoachAvailabilityForm, AppointmentRequestForm, AppointmentResponseForm, \
    PrivacySettingsForm, ProfilePictureForm
from .forms import CustomUserCreationForm, ArticleForm, RecipeForm, IngredientFormSet
from .forms import UpdateEmailForm, UpdatePasswordForm, ProfilePictureForm

# for calendar;
from django.http import JsonResponse
import json
from django.db import transaction

# Chatbot
import torch
from django.views.decorators.csrf import ensure_csrf_cookie
from .apps import CUFitnessConfig

# Appointment Making
import uuid
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta

# Messaging
from django.db.models import Q
from .models import Message
from .forms import MessageForm

# Fitness Challenges
from .models import Challenge, ChallengeParticipation
from .forms import ChallengeForm
from django.db.models import F

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
        # send coaches for user_home page to display them
        active_coaches = CustomUser.objects.filter(
            role="COACH",
            is_active=True
        ).order_by("first_name")
        return render(request, 'CUFitness/general_website/home.html', {"active_coaches": active_coaches})

# region all navbar pages
# -----------   Navbar Pages  -----------
def services(request):
    equipment = EquipmentList.objects.filter(is_active=True).order_by('name')
    total_items = sum(e.quantity for e in equipment)  # total number of equipment units
    context = {
        'equipment_list': equipment,
        'total_equipment_items': total_items,
    }
    return render(request, 'CUFitness/general_website/navbar/services.html', context)

def user_articles(request):
    free_articles = Article.objects.filter(locked=False)
    locked_articles = Article.objects.filter(locked=True)
    return render(request, 'CUFitness/general_website/navbar/articles.html', {"free_articles": free_articles, "locked_articles": locked_articles})

def workout_plans(request):
    return render(request, 'CUFitness/general_website/navbar/workout_plans.html')

def user_recipes(request):
    free_recipes = Recipe.objects.filter(locked=False)
    locked_recipes = Recipe.objects.filter(locked=True)
    return render(request, "CUFitness/general_website/navbar/recipes.html", {"free_recipes": free_recipes, "locked_recipes": locked_recipes})

def user_exercises(request):
    exercises = Exercise.objects.all().order_by('muscle_group')
    return render(request, "CUFitness/general_website/navbar/exercises.html", {"exercises": exercises})

# -----------   Dropdown Menu Pages  -----------
def amenities(request):
    return render(request, 'CUFitness/general_website/dropdown/amenities.html')

def schedule(request):
    return render(request, 'CUFitness/general_website/dropdown/schedule.html')

def contact(request):
    return render(request, 'CUFitness/general_website/dropdown/contact.html')

def about(request):
    return render(request, 'CUFitness/general_website/dropdown/about.html')

# -----------   Footer Pages  -----------
def faq(request):
    return render(request, 'CUFitness/general_website/faq.html')

def policy(request):
    return render(request, 'CUFitness/general_website/policy.html')
# endregion


# -----------   User Authentication   -----------

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
        email = request.POST['email'] # change these to whatever fields put in the form
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        # only log if coach
        if user is not None and user.role == 'COACH':
            login(request, user)
            # display the first_name of the logged-in user
            messages.success(request, 'You have been logged in as ' + user.first_name)

            return redirect('home') # cant write it as home.html because it's reverse searching for a template with the name "home"
        else:
            messages.error(request, 'Invalid Account Email or Password')
            return redirect('coach_login')
    else:
        return render(request, 'CUFitness/coach/coach_login.html') # render the HTML template on first visit


# -----------   User Profile & Account   -----------
@login_required(login_url='login')
def user_profile(request):
    # send each user's past/upcoming appointments with coaches
    now = timezone.now()
    # select_related('coach') avoids N+1 queries when displaying the coach's name in the template
    appointments = CoachAppointment.objects.filter(member=request.user).select_related('coach').order_by('start_time')
    upcoming_appointments = appointments.filter(start_time__gte=now).exclude(status='CANCELLED')
    past_appointments = appointments.filter(start_time__lt=now)
    canceled_appointments = appointments.filter(status='CANCELLED')

    context = {"upcoming_appointments":upcoming_appointments, "past_appointments":past_appointments, "canceled_appointments":canceled_appointments}

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
    # only delete if it's not the default
    if user.profile_picture and user.profile_picture.name != 'defaults/Default_Profile_Picture.jpg':
        user.profile_picture.delete(save=False)  # removes file from disk
    user.profile_picture = 'defaults/Default_Profile_Picture.jpg'
    user.save()
    return redirect('user_profile')

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_settings(request):
    # settings page for members and coaches — email, password, privacy, coach request.
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
    return render(request, 'CUFitness/user/user_settings.html', context)

@login_required(login_url='login')
@user_passes_test(lambda user: is_member(user) or is_coach(user))
def user_inbox(request):
    return render(request, 'CUFitness/user/user_inbox.html')

# @login_required(login_url='login')
# @user_passes_test(lambda user: is_member(user) or is_coach(user))
# def user_calendar(request):
#     """
#      Calendar page for members and coaches.
#
#      Members  → see their upcoming coach appointments (accepted & pending).
#      Coaches  → see their upcoming appointments *and* ALL their availability slots
#                 (past + future) so the calendar can render them for editing.
#      """
#     now = timezone.now()
#
#     if is_member(request.user):
#         upcoming_appointments = CoachAppointment.objects.filter(
#             member=request.user,
#             start_time__gte=now,
#             status__in=['PENDING', 'ACCEPTED'],
#         ).select_related('coach').order_by('start_time')
#
#         past_appointments = CoachAppointment.objects.filter(
#             member=request.user,
#             start_time__lt=now,
#         ).select_related('coach').order_by('-start_time')[:10]
#
#         availabilities = []
#
#     else:  # COACH
#         upcoming_appointments = CoachAppointment.objects.filter(
#             coach=request.user,
#             start_time__gte=now,
#             status__in=['PENDING', 'ACCEPTED'],
#         ).select_related('member').order_by('start_time')
#
#         past_appointments = CoachAppointment.objects.filter(
#             coach=request.user,
#             start_time__lt=now,
#         ).select_related('member').order_by('-start_time')[:10]
#
#         # ALL slots (past + future) so coaches can see/edit their full history
#         availabilities = CoachAvailability.objects.filter(
#             coach=request.user,
#         ).order_by('start_time')
#
#     # ── Build calendar event JSON ──────────────────────────────────
#     calendar_events = []
#
#     for appt in upcoming_appointments:
#         label = (
#             f"Session with {appt.member.first_name} {appt.member.last_name}"
#             if is_coach(request.user)
#             else f"Session with Coach {appt.coach.first_name} {appt.coach.last_name}"
#         )
#         color = '#15803d' if appt.status == 'ACCEPTED' else '#b45309'
#         calendar_events.append({
#             'type': 'appointment',
#             'title': label,
#             'start': appt.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
#             'end': appt.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
#             'color': color,
#             'status': appt.status,
#         })
#
#     for slot in availabilities:
#         calendar_events.append({
#             'type': 'availability',
#             'id': slot.id,
#             'title': 'Open Slot' if not slot.is_booked else 'Booked Slot',
#             'start': slot.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
#             'end': slot.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
#             'color': '#1d4ed8' if not slot.is_booked else '#6b7280',
#             'status': 'AVAILABLE' if not slot.is_booked else 'BOOKED',
#             'is_booked': slot.is_booked,
#         })
#
#     # Upcoming open slots for the sidebar list
#     upcoming_availabilities = [s for s in availabilities if s.start_time >= now and not s.is_booked]
#
#     context = {
#         'upcoming_appointments': upcoming_appointments,
#         'past_appointments': past_appointments,
#         'availabilities': upcoming_availabilities,
#         'calendar_events_json': json.dumps(calendar_events),
#         'is_coach': is_coach(request.user),
#     }
#     return render(request, 'CUFitness/user_profile/user_calendar.html', context)

@login_required(login_url='login')
def user_calendar(request):
    """
    Calendar page for members and coaches.

    Members  → see their upcoming coach appointments (accepted & pending).
    Coaches  → now redirected to user_coach_schedule.
    """
    if is_coach(request.user):
        return redirect('user_coach_schedule')

    now = timezone.now()

    # Member view
    upcoming_appointments = CoachAppointment.objects.filter(
        member=request.user,
        start_time__gte=now,
        status__in=['PENDING', 'ACCEPTED'],
    ).select_related('coach').order_by('start_time')

    past_appointments = CoachAppointment.objects.filter(
        member=request.user,
        start_time__lt=now,
    ).select_related('coach').order_by('-start_time')[:10]

    availabilities = []  # not used for members

    # Build calendar event JSON
    calendar_events = []
    for appt in upcoming_appointments:
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
        'availabilities': [],  # not used by member template
        'calendar_events_json': json.dumps(calendar_events),
        'is_coach': False,
    }
    return render(request, 'CUFitness/user/user_calendar.html', context)

@login_required(login_url='login')
@user_passes_test(is_coach)
def user_coach_schedule(request):
    now = timezone.now()

    # Confirmed appointments (accepted)
    confirmed = CoachAppointment.objects.filter(
        coach=request.user,
        start_time__gte=now,
        status='ACCEPTED'
    ).select_related('member').order_by('start_time')

    # Pending requests
    pending = CoachAppointment.objects.filter(
        coach=request.user,
        status='PENDING'
    ).select_related('member').order_by('start_time')

    # Auto-accept setting (must be added to CustomUser model)
    auto_accept = request.user.auto_accept_appointments

    # Upcoming availability (next 14 days, unbooked)
    upcoming_avail = CoachAvailability.objects.filter(
        coach=request.user,
        start_time__gte=now,
        start_time__lte=now + timedelta(days=14),
        is_booked=False
    ).order_by('start_time')

    # Gym info for the next 14 days (used to disable closed days in calendar)
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

    # Build calendar events for FullCalendar
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
        'auto_accept': auto_accept,
        'upcoming_avail': upcoming_avail,
        'calendar_events_json': json.dumps(calendar_events),
        'gym_settings': json.dumps(gym_info),   # template expects this name
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


# calendar
# ── AJAX: add availability slot ───────────────────────────────────
@login_required(login_url='login')
@user_passes_test(is_coach)
@require_POST
@ensure_csrf_cookie
def ajax_add_availability(request):
    """
    Create one or more availability slots for the logged-in coach.
    Expected JSON body:
    {
        "slots": [{"start": "ISO datetime", "end": "ISO datetime"}, ...],
        "recurrence": "none" | "weeks" | "indefinite",
        "recurrence_weeks": int (required if recurrence=="weeks")
    }
    Returns:
        {"created": count} or {"error": message}
    """
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

    # Determine number of weeks to generate
    max_weeks = 0
    if recurrence == 'weeks':
        max_weeks = recurrence_weeks
    elif recurrence == 'indefinite':
        max_weeks = 52  # generate a year's worth; can be adjusted

    now = timezone.now()

    # Pre-fetch gym settings for weekdays to avoid repeated DB hits
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
                start_dt = timezone.make_aware(start_dt)
            if timezone.is_naive(end_dt):
                end_dt = timezone.make_aware(end_dt)
        except ValueError:
            return JsonResponse({'error': 'Invalid datetime format in slot'}, status=400)

        # Validate each slot: not in the past, exactly one hour, within gym hours
        if start_dt < now:
            return JsonResponse({'error': f'Slot {start_dt} is in the past'}, status=400)
        if (end_dt - start_dt) != timedelta(hours=1):
            return JsonResponse({'error': 'Each slot must be exactly one hour'}, status=400)

        weekday = start_dt.weekday()
        gym = gym_info_cache.get(weekday)
        if not gym or not gym.is_open:
            return JsonResponse({'error': f'Gym closed on {start_dt.strftime("%A")}'}, status=400)
        if start_dt.time() < gym.open_time or end_dt.time() > gym.close_time:
            return JsonResponse({'error': f'Slot {start_dt.time()} outside gym hours'}, status=400)

        # For non‑recurring, create single slot
        if recurrence == 'none':
            # Check overlapping
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
            # Recurring: generate for each week up to max_weeks
            for week in range(max_weeks):
                slot_start = start_dt + timedelta(weeks=week)
                slot_end = end_dt + timedelta(weeks=week)

                # Skip if already exists (should not, but safety)
                if CoachAvailability.objects.filter(
                    coach=request.user,
                    start_time=slot_start,
                    end_time=slot_end
                ).exists():
                    continue

                # Check overlapping for each generated slot
                overlapping = CoachAvailability.objects.filter(
                    coach=request.user,
                    start_time__lt=slot_end,
                    end_time__gt=slot_start,
                    is_booked=False
                )
                if overlapping.exists():
                    # If overlapping, skip this week? Or abort? We'll skip to be safe.
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

    return JsonResponse({
        'created': len(created_slots),
        'recurrence_group': str(recurrence_group) if recurrence_group else None
    })

@login_required(login_url='login')
@user_passes_test(is_coach)
def ajax_edit_availability(request, slot_id):
    """Edit a single slot (only if unbooked)."""
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

    # Same validations as add
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

    # Check overlapping excluding self
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
    return JsonResponse({
        'id': slot.id,
        'start': slot.start_time.isoformat(),
        'end': slot.end_time.isoformat(),
    })


@login_required(login_url='login')
@user_passes_test(is_coach)
def ajax_delete_availability(request, slot_id):
    """Delete a single slot (only if unbooked)."""
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
    """Cancel all future unbooked slots in a recurring series."""
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
    expects a POST with 'action' = 'APPROVED' or 'REJECTED'.
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
        base = 'CUFitness/staff/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/general_website/base.html'
    else:
        base = 'CUFitness/general_website/base.html'

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
    #the following is needed to get the "display" tags, since multi-select-field doesn't have that functionality by default unlike charfield
    # Build a lookup dict from the choices and map the stored codes to labels
    choices_dict = dict(Recipe.DIETARY_CHOICES)
    dietary_display = [choices_dict.get(code, code) for code in recipe.dietary_restrictions]

    if request.user.is_authenticated:
        base = 'CUFitness/staff/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/general_website/base.html'
    else:
        base = 'CUFitness/general_website/base.html'

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






# --- Member Views ---

'''
# not needed anymore... coach list is displayed in home page
@login_required(login_url='login')
@user_passes_test(is_member)
def coach_list_view(request):
    coaches = CustomUser.objects.filter(role='COACH', is_active=True)

    # TODO need a html page to display the list of coach. change url if necessary
    return render(request, 'CUFitness/coach_list.html', {'coaches': coaches})

'''

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
    # View pending appointments and respond
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

# ======== Chatbot ===========

@ensure_csrf_cookie
def chatbot(request):
    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)

        from CUFitness.apps import get_chatbot_model
        tokenizer, model = get_chatbot_model()

        # Format the message using the model's chat template
        # TinyLlama chat expects messages in a list of dicts with "role" and "content"
        messages = [
            {"role": "user", "content": user_message}
        ]
        # Apply the chat template to get the full prompt
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100, # Response length limiter
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1
            )

        # Decode only the new tokens (skip the input prompt)
        new_tokens = outputs[0][inputs['input_ids'].shape[1]:]
        reply = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        # If reply is empty, provide a fallback
        if not reply:
            reply = "I'm not sure how to answer that."

        return JsonResponse({'reply': reply})

    # GET request – just render the empty chat page
    return render(request, 'CUFitness/chatbot.html')

# ==========Appointment API ========

@login_required
def api_coaches(request):
    """Return list of active coaches as JSON."""
    coaches = CustomUser.objects.filter(role='COACH', is_active=True).values('id', 'first_name', 'last_name')
    return JsonResponse(list(coaches), safe=False)


@login_required
def api_coach_availability(request):
    """Return available slots for a specific coach between start and end dates."""
    coach_id = request.GET.get('coach_id')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    if not coach_id or not start_date or not end_date:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        coach = CustomUser.objects.get(id=coach_id, role='COACH')
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Coach not found'}, status=404)

    slots = CoachAvailability.objects.filter(
        coach=coach,
        start_time__date__gte=start_date,
        start_time__date__lte=end_date,
        is_booked=False
    ).order_by('start_time').values('id', 'start_time', 'end_time')

    # Convert datetimes to ISO strings for JSON
    slot_list = []
    for slot in slots:
        slot_list.append({
            'id': slot['id'],
            'start_time': slot['start_time'].isoformat(),
            'end_time': slot['end_time'].isoformat(),
        })

    return JsonResponse(slot_list, safe=False)


@login_required
def api_all_availability(request):
    """Return all unbooked slots for a given date, with coach info."""
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Missing date'}, status=400)

    slots = CoachAvailability.objects.filter(
        start_time__date=date_str,
        is_booked=False
    ).select_related('coach').order_by('start_time')

    data = []
    for slot in slots:
        data.append({
            'id': slot.id,
            'coach_id': slot.coach.id,
            'coach_name': f"{slot.coach.first_name} {slot.coach.last_name}",
            'start_time': slot.start_time.isoformat(),
            'end_time': slot.end_time.isoformat(),
        })
    return JsonResponse(data, safe=False)


@login_required
@require_POST
@ensure_csrf_cookie
def api_request_appointment(request):
    """Create a new appointment request from a member."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    coach_id = data.get('coach_id')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    if not coach_id or not start_time_str or not end_time_str:
        return JsonResponse({'error': 'Missing fields'}, status=400)

    # Parse datetimes
    try:
        start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt)
        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt)
    except ValueError:
        return JsonResponse({'error': 'Invalid datetime format'}, status=400)

    # Check that the slot exists and is not booked
    try:
        availability = CoachAvailability.objects.get(
            coach_id=coach_id,
            start_time=start_dt,
            end_time=end_dt,
            is_booked=False
        )
    except CoachAvailability.DoesNotExist:
        return JsonResponse({'error': 'This time slot is no longer available'}, status=400)

    # Create the appointment
    appointment = CoachAppointment.objects.create(
        coach_id=coach_id,
        member=request.user,
        start_time=start_dt,
        end_time=end_dt,
        status='PENDING',
        availability=availability
    )

    # Mark the availability as booked
    availability.is_booked = True
    availability.save()

    return JsonResponse({'success': True, 'appointment_id': appointment.id})


@login_required(login_url='login')
def user_inbox(request):
    """Show inbox for the logged-in user (member or coach)."""
    user = request.user
    # Get messages where user is sender or recipient
    messages = Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).select_related('sender', 'recipient').order_by('-timestamp')

    if is_member(user):
        # For members: also provide list of coaches for sending new messages
        coaches = CustomUser.objects.filter(role='COACH', is_active=True).order_by('first_name')
        context = {
            'messages': messages,
            'coaches': coaches,
            'is_member': True,
        }
    else:
        # For coaches: only show messages, no coach list
        context = {
            'messages': messages,
            'is_member': False,
        }
    return render(request, 'CUFitness/user/user_inbox.html', context)

@login_required(login_url='login')
@user_passes_test(is_member)
def api_coach_search(request):
    """JSON endpoint for member to search coaches by name."""
    query = request.GET.get('q', '')
    coaches = CustomUser.objects.filter(
        role='COACH', is_active=True
    ).filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
    ).values('id', 'first_name', 'last_name', 'email')[:20]
    return JsonResponse(list(coaches), safe=False)

@login_required(login_url='login')
def send_message(request):
    """Handle sending a new message (member to coach)."""
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

    # Create message
    Message.objects.create(
        sender=request.user,
        recipient=recipient,
        subject=subject,
        body=body
    )
    messages.success(request, 'Message sent.')
    return redirect('user_inbox')

@login_required(login_url='login')
def reply_message(request, message_id):
    """Coach replies to a message they received."""
    original = get_object_or_404(Message, id=message_id, recipient=request.user)
    if request.method == 'POST':
        body = request.POST.get('body')
        if not body:
            messages.error(request, 'Message body cannot be empty.')
            return redirect('user_inbox')

        # Create reply (swap sender/recipient)
        Message.objects.create(
            sender=request.user,
            recipient=original.sender,
            subject=f"Re: {original.subject}",
            body=body
        )
        messages.success(request, 'Reply sent.')
        return redirect('user_inbox')
    else:
        # Show a simple form with original message quoted
        return render(request, 'CUFitness/user/user_coach_reply.html', {
            'original': original
        })

@login_required(login_url='login')
def mark_read(request, message_id):
    """Mark a message as read (AJAX)."""
    if request.method == 'POST':
        msg = get_object_or_404(Message, id=message_id, recipient=request.user)
        msg.is_read = True
        msg.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required(login_url='login')
@user_passes_test(is_coach)
@require_POST
def ajax_accept_appointment(request, appointment_id):
    appointment = get_object_or_404(CoachAppointment, id=appointment_id, coach=request.user, status='PENDING')
    appointment.status = 'ACCEPTED'
    appointment.save()
    return JsonResponse({'success': True})

@login_required(login_url='login')
@user_passes_test(is_coach)
@require_POST
def ajax_reject_appointment(request, appointment_id):
    appointment = get_object_or_404(CoachAppointment, id=appointment_id, coach=request.user, status='PENDING')
    # Optionally read a reason from POST data, but for simplicity we just reject
    appointment.status = 'REFUSED'
    appointment.save()
    return JsonResponse({'success': True})


## Fitness Challenges
@login_required(login_url='login')
def user_challenges(request):
    challenges = Challenge.objects.all()

    user_participation = ChallengeParticipation.objects.filter(user=request.user)
    joined_ids = user_participation.values_list('challenge_id', flat=True)

    # leaderboard (top users per challenge)
    leaderboard_data = []

    for challenge in Challenge.objects.all():
        participants_qs = ChallengeParticipation.objects.filter(challenge=challenge)
        
        participants = (
            participants_qs
            .select_related('user')
            .order_by('-progress')[:5]
        )

        top_participants = (
            participants_qs
            .select_related('user')
            .order_by('-progress')[:5]
        )

        leaderboard_data.append({
            'challenge': challenge,
            'participants' : participants,
            'top_participants': top_participants,
            'count': participants_qs.count()
        })

    return render(request, 'CUFitness/general_website/navbar/user_challenges.html', {
        'leaderboard_data': leaderboard_data,
        'challenges': challenges,
        'joined_ids': joined_ids,
        'participations': user_participation,
    })


@login_required(login_url='login')
def join_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)

    ChallengeParticipation.objects.get_or_create(
        user=request.user,
        challenge=challenge
    )

    return redirect('user_challenges')


@login_required(login_url='login')
def update_progress(request, participation_id):
    participation = get_object_or_404(
        ChallengeParticipation,
        id=participation_id,
        user=request.user
    )

    if request.method == "POST":
        increment = int(request.POST.get('progress', 0))

        participation.progress += increment

        # CAP the value
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

    return render(request, 'CUFitness/staff/challenges/challenges.html', {
        'challenges': challenges
    })

def challenge_detail(request, id):
    challenge = get_object_or_404(Challenge, id=id)

    if request.user.is_authenticated:
        base = 'CUFitness/staff/staff_base.html' if request.user.role == 'STAFF' else 'CUFitness/base.html'
    else:
        base = 'CUFitness/base.html'

    participants = ChallengeParticipation.objects.filter(
        challenge=challenge
    ).select_related('user').order_by('-progress')

    return render(request, 'CUFitness/staff/challenges/challenge_detail.html', {
        'challenge': challenge,
        'participants': participants,
        'base_template': base,
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
            return redirect('challenge_detail', id=challenge.id)
    else:
        form = ChallengeForm(instance=challenge)

    return render(request, 'CUFitness/staff/challenges/create_challenge.html', {
        'form': form,
        'challenge': challenge
    })

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

    return redirect('challenge_detail', id=id)