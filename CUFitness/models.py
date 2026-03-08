from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .managers import CustomUserManager



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

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

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


class Articles(models.Model):
    # cascade means that if user is deleted then article will be deleted as well
    # idk if we want that cause maybe we want to keep articles even staff are fired
   # user = models.ForeignKey(CustomUser, related_name="article", on_delete=models.CASCADE)
    author = models.ForeignKey(CustomUser, related_name="authors", on_delete=models.CASCADE)# links each article to unique user
    title = models.CharField(max_length=75)

    locked = models.BooleanField(default=False)

    description = models.CharField(max_length = 250, help_text="Add description here")
    body = models.TextField(help_text="Add body here")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f" {self.created_at:%Y-%m-%d %H:%M} - {self.updated_at:%Y-%m-%d %H:%M} - {self.author} - {self.title} - {self.body} - {self.locked} - {self.description}"
        )


class EquipmentList(models.Model):
    # Actual equipment list needs to be done in shell to make it add them one time.

    name = models.CharField(max_length=25, unique=True) #may not require unique to be true
    description = models.TextField(blank=True, help_text="Add description here")
    is_active = models.BooleanField(default=True, help_text="Uncheck when out of service")

    class Meta:
        verbose_name_plural = "Equipments"

    def __str__(self):
        return self.name

class EquipmentBooking(models.Model):
    equipment = models.ForeignKey(EquipmentList, on_delete=models.CASCADE, related_name='bookings')
    coach = models.ForeignKey('CustomUser', on_delete=models.CASCADE, limit_choices_to={'role': 'COACH'})
    member = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='training_sessions', null=True,
                               blank=True, help_text="Paid user being trained (optional)")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_cancelled = models.BooleanField(default=False)

    class Meta:
        ordering = ['start_time']
        # Prevent overlapping bookings for the same equipment
        constraints = [
            models.UniqueConstraint(
                fields=['equipment', 'start_time', 'end_time'],
                name='unique_booking_per_timeslot'
            )
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')

        overlapping = EquipmentBooking.objects.filter(
            equipment=self.equipment,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            is_cancelled=False
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError('This equipment is already booked during the selected time.')

    def save(self, *args, **kwargs):
        self.full_clean()  # runs validators including clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.equipment.name} booked by {self.coach.email} from {self.start_time} to {self.end_time}"


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

class CoachAppointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
        ('cancelled', 'Cancelled'),
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    refusal_reason = models.TextField(blank=True, help_text='Reason if refused')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')
        # Check coach is not double-booked (excluding pending? maybe only accepted)
        if self.status == 'accepted':
            overlapping = CoachAppointment.objects.filter(
                coach=self.coach,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
                status='accepted'
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError('Coach already has an accepted appointment during this time.')

    def __str__(self):
        return f"Appointment {self.member.email} with {self.coach.email} - {self.status}"

    def save(self, *args, **kwargs):
        self.full_clean()   # runs validators including clean()
        super().save(*args, **kwargs)


# Placeholder for review and report

# class CoachReview(models.Model):
#     def __str__(self):
#         return None
#
# class CoachReport(models.Model):
#
#     def __str__(self):
#         return None