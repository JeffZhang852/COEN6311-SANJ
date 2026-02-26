from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
#May need
from django.db.models.signals import post_save
from django.dispatch import receiver

"""Profile"""

# Make different roles
class Profile(models.Model):
    ROLE_CHOICES = (
        ('user', 'Gym User'),
        ('coach', 'Coach'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default='user')
    def __str__(self):
        return f"{self.user.username}-{self.role}"

"""Following part is optional for profile making"""
# On user creation automatically give option for user. may not need if coach ONLY need coach profile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


"""Scheduler making"""
class User_Scheduler(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profile_role':'coach'})
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_reserved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.teacher.username}-{self.start_time} to {self.end_time}"

class Equipment_Checker(models.Model):
    name = models.CharField(max_length=50)
    description =  models.TextField(blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Equipment_Scheduler(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipment_scheduling')
    equipment = models.ForeignKey(Equipment_Checker, on_delete=models.CASCADE, related_name='scheduling')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    scheduled_at = models.DateTimeField(auto_now_add=True)

    class Check_Schedule:
        constraints = [
            models.UniqueConstraint(fields=['equipment', 'start_time'], name='unique_equipment_booking')
        ]
        def __str__(self):
            return f"{self.user.username} - {self.equipment.name} ({self.start_time})"
