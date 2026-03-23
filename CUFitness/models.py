from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .managers import CustomUserManager
from multiselectfield import MultiSelectField
import uuid
from decimal import Decimal
from .managers import CustomUserManager

#=====================================================
#========    Universal Models (Setups)     ===========
#region===============================================
# Main user role control
class CustomUser(AbstractBaseUser, PermissionsMixin):
    # List of roles, defaulting all to members
    # Coach needs to request, staff and admin are done in backend
    ROLE_CHOICES = [
        ('MEMBER', 'Member'),
        ('COACH', 'Coach'),
        ('STAFF', 'Staff'),
        ('ADMIN', 'Admin'),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='MEMBER',
        verbose_name='user role'
    )

    # Membership variations
    MEMBERSHIP_CHOICES = [
        ("BASIC", "Basic"),
        ("STANDARD", "Standard"),
        ("PLATINUM", "Platinum"),
        ("PER_SESSION", "Per Session"),
    ]
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=50, default='')
    last_name = models.CharField(_("last name"), max_length=50, default='')
    membership= models.CharField(_("membership"), max_length=50, choices=MEMBERSHIP_CHOICES,default='BASIC')

    phone_number = models.CharField(max_length=20, default='', help_text='e.g. +1 514 555 0123')
    date_of_birth = models.DateField(null=True, help_text='Format: YYYY-MM-DD')
    address = models.CharField(max_length=255, default='', blank=True, help_text='Address here')

    # Coach appointment request
    REQUEST_STATUS_CHOICES = [
        ('NONE', 'No Request'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    coach_request_status = models.CharField(
        max_length=20,
        choices=REQUEST_STATUS_CHOICES,
        default='NONE',
        verbose_name='Coach request status'
    )

    # User privacy control
    WORKOUT_VISIBILITY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('COACH_ONLY', 'Coach Only'),
    ]
    workout_visibility = models.CharField(
        max_length=20,
        choices=WORKOUT_VISIBILITY_CHOICES,
        default='COACH_ONLY',
        verbose_name='Workout history privacy setting'
    )
    # Option for coach to auto accept first demand for appointment
    auto_accept_appointments = models.BooleanField(
        default=False,
        help_text='Automatically accept all incoming appointment requests'
    )

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    # override save() to auto-sync is_staff from role.
    # when a user's role changes (coach promotion, staff assignment, etc.), is_staff is automatically kept correct
    def save(self, *args, **kwargs):
        # Keep Django's is_staff flag in sync with the role field
        self.is_staff = self.role in ('STAFF', 'ADMIN')
        super().save(*args, **kwargs)
    def __str__(self):
        return self.email

    class Meta:
        permissions = [
            ("can_ban_users", "Can ban users"),
            ("can_view_coach_requests", "Can view coach requests"),
            ("can_accept_coach_requests", "Can accept coach requests"),
            ("can_change_user_role", "Can change user role"),
            ("can_view_user_reports", "Can view user reports"),
        ]

# Articles
class Article(models.Model):
    # cascade means that if user is deleted then article will be deleted as well
    # idk if we want that cause maybe we want to keep articles even staff are fired
    # changed on_delete so that if the authro is deleted the article stays in database but has its authro as null
    #now need to handle author is null in the templates
    author = models.ForeignKey(
        CustomUser, related_name="articles",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=100)

    locked = models.BooleanField(default=False, help_text='Premium content — requires login to view',)

    description = models.CharField(max_length = 250, help_text='Brief summary of the article')
    body = models.TextField(help_text="Add body here")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# what the admin sees on the article list page
    def __str__(self):
        return (
            f" {self.created_at:%Y-%m-%d %H:%M} - {self.updated_at:%Y-%m-%d %H:%M} - {self.author} - {self.title} - {self.locked} - {self.description}"
        )

# List of equipments, used for equipment availability check and coach's equipment reservation
class EquipmentList(models.Model):
    name = models.CharField(max_length=25, unique=True)
    description = models.TextField(blank=True, help_text="Add description here")
    quantity = models.PositiveIntegerField(default=1, help_text="Number of units available")
    is_active = models.BooleanField(default=True, help_text="Uncheck when out of service")

    class Meta:
        verbose_name_plural = "Equipments"

    def __str__(self):
        return self.name

# Recipe Models
class Recipe(models.Model):
    DIFFICULTY_CHOICES = [
        ('EASY',   'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD',   'Hard'),
    ]
    DIETARY_CHOICES = [
        ('NO_NUTS', 'No Nuts'),
        ('NO_SEAFOOD', 'No Seafood'),
        ('NO_DAIRY_LACTOSE', 'No Dairy Lactose'),
        ('NO_RED_MEAT', 'No Red Meat'),
        ('NO_PORK', 'No Pork'),
        ('NO_ALCOHOL', 'No Alcohol'),
        ('NO_SHELLFISH', 'No Shellfish'),
        ('NO_GLUTEN', 'No Gluten'),
        ('NO_SESAME', 'No Sesame'),
        ('NO_MUSTARD', 'No Mustard'),
        ('VEGAN', 'Vegan'),
        ('VEGETARIAN', 'Vegetarian'),
    ]

    author = models.ForeignKey(
        CustomUser,
        related_name='recipes',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=250, help_text='Brief summary of the recipe')
    locked = models.BooleanField(
        default=False,
        help_text='Premium content — requires login to view',
    )

    # Recipe-specific fields
    prep_time_minutes = models.PositiveIntegerField(help_text='Preparation time in minutes')
    cook_time_minutes = models.PositiveIntegerField(help_text='Cooking time in minutes (0 if none)')
    servings = models.PositiveIntegerField(default=1)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    instructions = models.TextField(help_text='Step-by-step cooking instructions')
    calories_per_serving = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Approximate calories per serving (optional)',
    )
    dietary_restrictions = MultiSelectField(choices=DIETARY_CHOICES, blank=True, max_length=250, help_text='Dietary choices (optional)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

# calls the scale ingredient function from here (helper method)
# recipe.scaled_ingredients(2)  # returns [(ingredient, scaled_qty), ...]
# i dont think we need it tbh
#just added work for no reason
    def scaled_ingredients(self, factor):
        return [
            (ing, ing.scaled_quantity(factor))
            for ing in self.ingredients.all()
        ]

    def __str__(self):
        return f'{self.title} (serves {self.servings}) — {self.get_difficulty_display()}'

    @property
    def total_time_minutes(self):
        return self.prep_time_minutes + self.cook_time_minutes

class RecipeIngredient(models.Model):
    UNIT_CHOICES = [
        # Volume
        ('TSP', 'tsp'),
        ('TBSP', 'tbsp'),
        ('CUP', 'cup'),
        ('ML', 'ml'),
        ('L', 'l'),
        ('FL_OZ', 'fl oz'),
        # Weight
        ('G', 'g'),
        ('KG', 'kg'),
        ('OZ', 'oz'),
        ('LB', 'lb'),
        # Count
        ('WHOLE', 'whole'),
        ('PINCH', 'pinch'),
        ('SLICE', 'slice'),
        # Free text fallback
        ('OTHER', 'other'),
    ]
    recipe = models.ForeignKey(Recipe, related_name='ingredients', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=7, decimal_places=2, help_text='e.g. 1.5, 100, 0.25')
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='OTHER')
    unit_other = models.CharField(max_length=50, blank=True, help_text='Describe unit if "other" selected')

    notes = models.CharField(max_length=100, blank=True, help_text='e.g. "finely chopped", "optional"')

# this is used to scale the recipe to different serving sizes
    def scaled_quantity(self, factor):
        return self.quantity * Decimal(str(factor))

    class Meta:
        ordering = ['id']  # preserve the order ingredients were added

    def __str__(self):
        base = f'{self.quantity} {self.name}'
        return f'{base} ({self.notes})' if self.notes else base

# WorkoutPlan ──< WorkoutPlanExercise >── Exercise

class Exercise(models.Model):
    DIFFICULTY_CHOICES = [
        ('EASY',   'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD',   'Hard'),
    ]
    MUSCLE_CHOICES = [
        ('CHEST', 'Chest'),
        ('BACK', 'Back'),
        ('LEGS', 'Legs'),
        ('SHOULDERS', 'Shoulders'),
        ('ARMS', 'Arms'),
        ('CORE', 'Core'),
        ('FULL_BODY', 'Full Body'),
    ]
    GOAL_CHOICES = [
        ('', ''),
        ('STRENGTH', 'Strength'),
        ('CARDIO', 'Cardio'),
        ('FLEXIBILITY', 'Flexible'),
        ('WEIGHT_LOSS', 'Weight Loss'),
        ('MUSCLE_GAIN', 'Muscle Gain'),
    ]

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=250, help_text='Brief summary of the exercise')
    instructions = models.TextField(help_text='Step-by-step instructions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, related_name='exercises', on_delete=models.CASCADE)

    muscle_group = models.CharField(choices=MUSCLE_CHOICES, max_length=30, blank=True, null=True)
    difficulty = models.CharField(choices=DIFFICULTY_CHOICES, max_length=25, blank=True, null=True)
    goal = models.CharField(max_length=15, choices=GOAL_CHOICES, default='')

    equipment = models.ManyToManyField(EquipmentList , related_name='exercises', blank=True)
    def __str__(self):
        return self.title

class WorkoutPlan(models.Model):
    DIFFICULTY_CHOICES = [
        ('EASY',   'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD',   'Hard'),
    ]
    GOAL_CHOICES = [
        ('', ''),
        ('STRENGTH', 'Strength'),
        ('CARDIO', 'Cardio'),
        ('FLEXIBILITY', 'Flexible'),
        ('WEIGHT_LOSS', 'Weight Loss'),
        ('MUSCLE_GAIN', 'Muscle Gain'),
    ]

    author = models.ForeignKey(
        CustomUser,
        related_name='workouts',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    title = models.CharField(max_length=100)

    locked = models.BooleanField(default=False, help_text='Premium content — requires login to view', )

    description = models.CharField(max_length=100, help_text='Brief summary of the workout plan')
    body = models.TextField(help_text='Detailed overview of the plan')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    duration_minutes= models.PositiveIntegerField(default=0)
    goal = models.CharField(max_length=15, choices=GOAL_CHOICES, default='')
    def __str__(self):
        return f'{self.title} — {self.get_goal_display()}'

class WorkoutPlanExercise(models.Model):
    workout = models.ForeignKey(WorkoutPlan, related_name='exercises', on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, related_name='workout_plans', on_delete=models.CASCADE)
    sets = models.PositiveIntegerField(default=0)
    reps = models.CharField(max_length=20, default='0', help_text='e.g. "10" or "8-12"')
    rest_seconds = models.PositiveIntegerField(default=60)
    order = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.exercise.title} in {self.workout.title}'

#endregion

#=====================================================
#=======Role Specific-Admin/Staff     ===============
#region===============================================
class GymInfo(models.Model):
    """
    Stores opening/closing times for each day of the week.
    One record per day (unique). Admin can configure which days the gym is open
    and what hours. Used by coaches when adding availability slots.
    """
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6
    DAY_CHOICES = [
        (MONDAY, 'Monday'),
        (TUESDAY, 'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY, 'Thursday'),
        (FRIDAY, 'Friday'),
        (SATURDAY, 'Saturday'),
        (SUNDAY, 'Sunday'),
    ]

    day = models.IntegerField(choices=DAY_CHOICES, unique=True)
    open_time = models.TimeField(null=True, blank=True, help_text='Opening time (leave blank if closed)')
    close_time = models.TimeField(null=True, blank=True, help_text='Closing time (leave blank if closed)')
    is_open = models.BooleanField(default=True, help_text='Uncheck to mark the gym closed all day')

    class Meta:
        ordering = ['day']
        verbose_name_plural = 'Gym Information'

    def __str__(self):
        day_name = self.get_day_display()
        if not self.is_open:
            return f"{day_name}: Closed"
        # If open but times missing, show a warning
        if self.open_time and self.close_time:
            return f"{day_name}: {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')}"
        return f"{day_name}: Open (hours not set)"

#endregion

#=====================================================
#=======Role Specific-Coach     ===============
#region===============================================
class CoachAvailability(models.Model):
    coach = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'COACH'},
        related_name='availabilities'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)

    # NEW FIELDS for recurring slots
    is_recurring = models.BooleanField(
        default=False,
        help_text='If True, this slot repeats weekly'
    )
    recurrence_group = models.UUIDField(
        null=True, blank=True,
        help_text='UUID to group recurring slots (all slots in a series share the same UUID)'
    )

    class Meta:
        ordering = ['start_time']
        verbose_name_plural = 'Coach availabilities'

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')
        # No overlapping availability for same coach
        overlapping = CoachAvailability.objects.filter(
            coach=self.coach,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError('Availability slots cannot overlap.')

    def __str__(self):
        return f"{self.coach.email}: {self.start_time} - {self.end_time}"

    def save(self, *args, **kwargs):
        self.full_clean()   # runs validators including clean()
        super().save(*args, **kwargs)

    # Prevent deletion of booked slots
    def delete(self, *args, **kwargs):
        if self.is_booked:
            raise ValidationError("Cannot delete a booked availability slot.")
        super().delete(*args, **kwargs)

class CoachAppointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REFUSED', 'Refused'),
        ('CANCELLED', 'Cancelled'),
    ]
    coach = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'COACH'},
        related_name='coach_appointments'
    )
    member = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'MEMBER'},
        related_name='member_appointments'
    )
    availability = models.OneToOneField(
        CoachAvailability,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Linked availability slot'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    refusal_reason = models.TextField(blank=True, help_text='Reason if refused')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')
        # Check coach is not double-booked (excluding pending? maybe only accepted)
        if self.status == 'ACCEPTED':
            overlapping = CoachAppointment.objects.filter(
                coach=self.coach,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
                status='ACCEPTED'
            )
            if self.pk: # exclude self when updating an existing record
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError(
                    f'Coach already has an accepted appointment between '
                    f'{self.start_time} and {self.end_time}.'
                )

    def __str__(self):
        return f"Appointment {self.member.email} with {self.coach.email} - {self.status}"

    def save(self, *args, **kwargs):
        self.full_clean()   # runs validators including clean()
        super().save(*args, **kwargs)

#endregion

#=====================================================
#=======Role Specific-User     ===============
#=====================================================
class Message(models.Model):
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    subject = models.CharField(max_length=200)
    body = models.TextField(max_length=3000)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    # Optional: parent field for threading, optional. see if the thing works
    # parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.subject[:20]}"


# optional feature: Placeholder
# class CoachReview(models.Model):
#     def __str__(self):
#         return None
#
# class CoachReport(models.Model):
#
#     def __str__(self):
#         return None