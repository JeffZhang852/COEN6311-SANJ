
# for user model

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager




class CustomUser(AbstractBaseUser, PermissionsMixin):
    MEMBERSHIP_CHOICES = [
        ("BASIC", "Basic"),
        ("STANDARD", "Standard"),
        ("PLATINUM", "Platinum"),
        ("PER SESSION", "Per Session"),
    ]
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=50, default='')
    last_name = models.CharField(_("last name"), max_length=50, default='')
    membership= models.CharField(_("membership"), max_length=50, choices=MEMBERSHIP_CHOICES,)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


