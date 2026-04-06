# Standard library
from datetime import datetime
from decimal import Decimal

# Third-party
from multiselectfield import MultiSelectField

# Django
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Local
from .managers import CustomUserManager

#=====================================================
#========    Universal Models (Setups)     ===========
#region===============================================
# Standard user role creation.
class CustomUser(AbstractBaseUser, PermissionsMixin):
    # List of roles, defaulting all to members
    # Coach needs to request, staff and admin are done in backend
    ROLE_CHOICES = [
        ('MEMBER', 'Member'),
        ('COACH', 'Coach'),
        ('STAFF', 'Staff'),
        ('ADMIN', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER', verbose_name='user role')

    # Subscription level
    MEMBERSHIP_CHOICES = [
        ("BASIC", "Basic"),
        ("STANDARD", "Standard"),
        ("PLATINUM", "Platinum"),
        ("PER_SESSION", "Per Session"),
    ]

    # User profile contents
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=50, default='')
    last_name = models.CharField(_("last name"), max_length=50, default='')
    membership = models.CharField(_("membership"), max_length=50, choices=MEMBERSHIP_CHOICES, default='BASIC')
    phone_number = models.CharField(max_length=20, default='', help_text='e.g. +1 514 555 0123')
    date_of_birth = models.DateField(null=True,)
    address = models.CharField(max_length=255, default='', blank=True,)

    # Profile picture — optional, defaults to the generic silhouette
    #upload_to='profile_pictures/' means uploaded photos go to MEDIA_ROOT/profile_pictures/
    # default='defaults/...' points to the fallback image inside MEDIA_ROOT
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='defaults/Default_Profile_Picture.jpg',blank=True,)

    # Coach request handling
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

    # User privacy setting for workout visibility
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

    # Django authentication control
    is_staff = models.BooleanField(default=False)   # Staff access
    is_active = models.BooleanField(default=True)   # Account deactivation control
    date_joined = models.DateTimeField(default=timezone.now)

    # Authentication configuration
    USERNAME_FIELD = "email"    # Use email as login
    REQUIRED_FIELDS = []    # Safety control for createsuperuser

    # Custom user manager
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        # Automatically sync is_staff with role STAFF or ADMIN. Both get staff access
        self.is_staff = self.role in ('STAFF', 'ADMIN')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    # Coach Review Control
    # Calculate average rating based on review
    def average_rating(self):
        if self.role != 'COACH':
            return 0
        reviews = self.received_reviews.all()
        if not reviews:
            return 0
        total = sum(r.rating for r in reviews)
        return round(total / reviews.count(), 1)
    # To display latest reviews. New to old. Max 5
    def latest_reviews(self, limit=5):
        if self.role != 'COACH':
            return CoachReview.objects.none()
        return self.received_reviews.order_by('-created_at')[:limit]
    # Count reviews for payment calculation
    def total_reviews_count(self):
        if self.role != 'COACH':
            return 0
        return self.received_reviews.count()
    # Review checker. 1 user can review once PER appointment per coach. More appointment = more review for user to coach
    def has_reviewed_appointment(self, appointment):
        if self.role != 'MEMBER':
            return False
        return CoachReview.objects.filter(member=self, appointment=appointment).exists()

    # Salary calculation
    # (15$ base + 2$ x user review score) x hour worked per month
    # This function returns how many hours coach will work
    def total_accepted_hours_current_month(self):
        from .models import CoachAppointment # Circular import to avoid order problem and retain code structure
        now = timezone.now()
        year = now.year
        month = now.month
        start_of_month = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
        else:
            end_of_month = datetime(year, month + 1, 1, tzinfo=timezone.get_current_timezone())

        count = CoachAppointment.objects.filter(
            coach=self,
            status='ACCEPTED',
            end_time__gte=start_of_month,
            end_time__lt=end_of_month
        ).count()

        return float(count)  # each appointment = 1 hour

    class Meta:
        permissions = [
            ("can_ban_users", "Can ban users"),
            ("can_view_coach_requests", "Can view coach requests"),
            ("can_accept_coach_requests", "Can accept coach requests"),
            ("can_change_user_role", "Can change user role"),
            ("can_view_user_reports", "Can view user reports"),
        ]

# User generated articles for the website
class Article(models.Model):
    # Author of the article. If the author is deleted, keep the article but set author to NULL
    # The template must handle author = None (e.g., show "Former Staff" or "Unknown")
    author = models.ForeignKey(
        CustomUser, related_name="articles",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=100)

    # Premium content control – requires login if True
    locked = models.BooleanField(default=False, help_text='Premium content — requires login to view')
    description = models.CharField(max_length=250, help_text='Brief summary of the article')
    body = models.TextField(help_text="Add body here")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f" {self.created_at:%Y-%m-%d %H:%M} - {self.updated_at:%Y-%m-%d %H:%M} - {self.author} - {self.title} - {self.locked} - {self.description}"
        )

# List of equipments
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
    # Difficulty levels filter
    DIFFICULTY_CHOICES = [
        ('EASY',   'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD',   'Hard'),
    ]
    # Dietary restriction tags
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
    # Author of the recipe. Keep recipe if author deleted (set NULL)
    author = models.ForeignKey(CustomUser, related_name='recipes', on_delete=models.SET_NULL, null=True, blank=True,)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=250, help_text='Brief summary of the recipe')
    # Premium content – requires login if True
    locked = models.BooleanField(default=False, help_text='Premium content — requires login to view',)
    # Recipe‑specific fields
    prep_time_minutes = models.PositiveIntegerField(help_text='Preparation time in minutes')
    cook_time_minutes = models.PositiveIntegerField(help_text='Cooking time in minutes (0 if none)')
    servings = models.PositiveIntegerField(default=1)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    instructions = models.TextField(help_text='Step-by-step cooking instructions')
    calories_per_serving = models.PositiveIntegerField(null=True, blank=True, help_text='Approximate calories per serving (optional)',)
    dietary_restrictions = MultiSelectField(choices=DIETARY_CHOICES, blank=True, max_length=250, help_text='Dietary choices (optional)')
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']   # Newest first

    # Helper method to scale ingredients for different serving sizes
    # Returns list of (ingredient, scaled_quantity) tuples.
    # Note: Currently not used, kept for potential future scaling feature.
    def scaled_ingredients(self, factor):
        return [
            (ing, ing.scaled_quantity(factor))
            for ing in self.ingredients.all()
        ]

    def __str__(self):
        return f'{self.title} (serves {self.servings}) — {self.get_difficulty_display()}'

    # Compute total cook time, used in templates
    @property
    def total_time_minutes(self):
        return self.prep_time_minutes + self.cook_time_minutes

# Individual ingredient within a recipe
class RecipeIngredient(models.Model):
    # Unit of measurement choices
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
    # Parent recipe – cascade delete removes ingredients when recipe is deleted
    recipe = models.ForeignKey(Recipe, related_name='ingredients', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=7, decimal_places=2, help_text='e.g. 1.5, 100, 0.25')
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='OTHER')
    unit_other = models.CharField(max_length=50, blank=True, help_text='Describe unit if "other" selected')

    # Optional notes
    notes = models.CharField(max_length=100, blank=True, help_text='e.g. "finely chopped", "optional"')

    # Scale ingredient quantity by a factor
    def scaled_quantity(self, factor):
        return self.quantity * Decimal(str(factor))

    class Meta:
        ordering = ['id']   # Preserve the order ingredients were added (by insertion)

    def __str__(self):
        base = f'{self.quantity} {self.name}'
        return f'{base} ({self.notes})' if self.notes else base

# Individual exercise for workout plans
class Exercise(models.Model):
    # Difficulty levels
    DIFFICULTY_CHOICES = [
        ('EASY',   'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD',   'Hard'),
    ]
    # Primary muscle group targeted
    MUSCLE_CHOICES = [
        ('CHEST', 'Chest'),
        ('BACK', 'Back'),
        ('LEGS', 'Legs'),
        ('SHOULDERS', 'Shoulders'),
        ('ARMS', 'Arms'),
        ('CORE', 'Core'),
        ('FULL_BODY', 'Full Body'),
    ]
    # Fitness goal associated with the exercise
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

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional categorization fields
    muscle_group = models.CharField(choices=MUSCLE_CHOICES, max_length=30, blank=True, null=True)
    difficulty = models.CharField(choices=DIFFICULTY_CHOICES, max_length=25, blank=True, null=True)
    goal = models.CharField(max_length=15, choices=GOAL_CHOICES, default='')

    # Equipment required for this exercise
    equipment = models.ManyToManyField(EquipmentList, related_name='exercises', blank=True)

    def __str__(self):
        return self.title

# A collection of exercises forming a complete workout routine
class WorkoutPlan(models.Model):
    # Difficulty level of the overall plan
    DIFFICULTY_CHOICES = [
        ('EASY',   'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD',   'Hard'),
    ]
    # Primary fitness goal of the plan
    GOAL_CHOICES = [
        ('', ''),
        ('STRENGTH', 'Strength'),
        ('CARDIO', 'Cardio'),
        ('FLEXIBILITY', 'Flexible'),
        ('WEIGHT_LOSS', 'Weight Loss'),
        ('MUSCLE_GAIN', 'Muscle Gain'),
    ]
    # Author who created the plan. Keep plan if author deleted (set NULL)
    author = models.ForeignKey(
        CustomUser,
        related_name='workouts',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    title = models.CharField(max_length=100)

    # Premium content – requires login if True
    locked = models.BooleanField(default=False, help_text='Premium content — requires login to view')

    description = models.CharField(max_length=100, help_text='Brief summary of the workout plan')
    body = models.TextField(help_text='Detailed overview of the plan')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Plan attributes
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    duration_minutes = models.PositiveIntegerField(default=0)
    goal = models.CharField(max_length=15, choices=GOAL_CHOICES, default='')

    def __str__(self):
        return f'{self.title} — {self.get_goal_display()}'

# List of exercise per plan
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

# Fitness challenge created by staff
class Challenge(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    # Target value to complete the challenge
    goal_target = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    # Staff who created the challenge. Keep challenge if creator deleted (set NULL)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# Tracks a user's progress in a specific challenge
class ChallengeParticipation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    # Current progress toward goal_target
    progress = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'challenge')   # One participation per user per challenge

    # Calculate percentage completed capped at 100%
    def progress_percentage(self):
        if self.challenge.goal_target == 0:
            return 0
        return min(100, int((self.progress / self.challenge.goal_target) * 100))

# Allows user to send msg to coach if they had appointment.
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

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.subject[:20]}"

class ContactMessage(models.Model):
    # no need for sender/recipient because any user can send support messages and all staff can see them
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=250)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        ordering = ['-created_at']
#endregion

#=====================================================
#=======Role Specific-Admin/Staff     ===============
#region===============================================
# Gym's opening day and hour
class GymInfo(models.Model):
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
    is_open_24h = models.BooleanField(default=False, help_text='Check if the gym is open 24 hours on this day')

    class Meta:
        ordering = ['day']
        verbose_name_plural = 'Gym Information'

    def __str__(self):
        day_name = self.get_day_display()
        if not self.is_open:
            return f"{day_name}: Closed"
        if self.is_open_24h:
            return f"{day_name}: Open 24 Hours"
        if self.open_time and self.close_time:
            return f"{day_name}: {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')}"
        return f"{day_name}: Open (hours not set)"
#endregion

#=====================================================
#=======Role Specific-Coach     ===============
#region===============================================
# Coach's availability. Can add if GYM opens in GYM Information.
class CoachAvailability(models.Model):
    # Coach who owns this availability slot
    coach = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'COACH'},
        related_name='availabilities'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    # Whether this slot has been booked by a member
    is_booked = models.BooleanField(default=False)
    # Recurring slot fields
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

    # Validate time range and prevent overlapping slots for the same coach
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')
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

    # Run validation on every save
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # Prevent deletion of slots that are already booked
    def delete(self, *args, **kwargs):
        if self.is_booked:
            raise ValidationError("Cannot delete a booked availability slot.")
        super().delete(*args, **kwargs)

# User send coach appointment based on their availability
class CoachAppointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REFUSED', 'Refused'),
        ('CANCELLED', 'Cancelled'),
    ]
    # Coach assigned to this appointment
    coach = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'COACH'},
        related_name='coach_appointments'
    )
    # Member who booked the appointment
    member = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'MEMBER'},
        related_name='member_appointments'
    )
    # Link to the original availability slot (optional, kept for reference)
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

    # Validate time range and prevent double‑booking for accepted appointments
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')
        if self.status == 'ACCEPTED':
            overlapping = CoachAppointment.objects.filter(
                coach=self.coach,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
                status='ACCEPTED'
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError(
                    f'Coach already has an accepted appointment between '
                    f'{self.start_time} and {self.end_time}.'
                )

    def __str__(self):
        return f"Appointment {self.member.email} with {self.coach.email} - {self.status}"

    # Run validation on every save
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# User write review to coach. Intended for past appointment only
# Realistically, I allowed to write review even for upcoming to confirm utility.
class CoachReview(models.Model):
    # Coach being reviewed
    coach = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_reviews',
        limit_choices_to={'role': 'COACH'}
    )
    # Member who wrote the review
    member = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='written_reviews',
        limit_choices_to={'role': 'MEMBER'}
    )
    # One review per appointment, but one user can write multiple per multi appointment per coach
    appointment = models.OneToOneField(
        'CoachAppointment',
        on_delete=models.CASCADE,
        related_name='review'
    )
    # Rating from 1 to 5 stars
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 to 5 stars'
    )
    # Optional comment max 500 characters
    comment = models.TextField(max_length=500, blank=True, help_text='Optional comment (max 500 characters)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Coach Review'
        verbose_name_plural = 'Coach Reviews'

    def __str__(self):
        return f"Review by {self.member.email} for {self.coach.email} – {self.rating}★"
#endregion

