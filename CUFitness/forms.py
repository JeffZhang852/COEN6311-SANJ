from django import forms

from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser,CoachAppointment,CoachAvailability, ContactMessage
from .models import Article, Recipe, RecipeIngredient, GymInfo, Message, Challenge
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", 'phone_number', 'date_of_birth', 'address', 'membership')
        # dropdown membership selection
        widgets = {
            'membership': forms.Select(attrs={
                'class': 'styled-select'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class UpdateEmailForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Make sure no other user already has this email
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

class UpdatePasswordForm(PasswordChangeForm):
    # PasswordChangeForm already handles old/new/confirm password validation
    pass

class CoachRequestForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = []  # No need to send stuff. May add notification via email later if needed.

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_picture']

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title','description', 'body', 'locked']
        exclude = ["author"] # we set it manually
        widgets = {}

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            'title', 'description', 'difficulty',
            'prep_time_minutes', 'cook_time_minutes',
            'servings', 'calories_per_serving',
            'instructions',
            'dietary_restrictions', 'locked',
        ]

IngredientFormSet = inlineformset_factory(
    parent_model=Recipe,
    model=RecipeIngredient,
    fields=['name', 'quantity', 'unit', 'notes'],
    extra=3,        # show 3 empty ingredient rows by default
    can_delete=True,
)


class CoachAvailabilityForm(forms.ModelForm):
    class Meta:
        model = CoachAvailability
        fields = ['start_time', 'end_time', 'is_recurring']

    def __init__(self, *args, **kwargs):
        self.coach = kwargs.pop('coach', None)
        self.selected_date = kwargs.pop('selected_date', None)  # date object
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        if start and end:
            # Must be same day and exactly one hour
            if start.date() != end.date():
                raise ValidationError("Start and end must be on the same day.")
            if (end - start) != timedelta(hours=1):
                raise ValidationError("Slot must be exactly one hour.")
            # Check against gym hours
            weekday = start.weekday()
            try:
                gym_day = GymInfo.objects.get(day=weekday)
                if not gym_day.is_open:
                    raise ValidationError("Gym is closed on this day.")
                if start.time() < gym_day.open_time or end.time() > gym_day.close_time:
                    raise ValidationError("Slot must be within gym operating hours.")
            except GymInfo.DoesNotExist:
                raise ValidationError("Gym hours not configured for this day.")
        return cleaned

class AppointmentRequestForm(forms.ModelForm):
    class Meta:
        model = CoachAppointment
        fields = ['start_time', 'end_time']  # member chooses time
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.coach = kwargs.pop('coach', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and self.coach:
            # Check if slot is within coach's availability and not overlapping accepted
            # (This can be more sophisticated; simple validation here)
            # For now, we'll rely on view logic to provide only available slots via a dropdown
            pass
        return cleaned_data

class AppointmentResponseForm(forms.ModelForm):
    class Meta:
        model = CoachAppointment
        fields = ['status', 'refusal_reason']
        widgets = {
            'refusal_reason': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        status = self.cleaned_data.get('status')
        reason = self.cleaned_data.get('refusal_reason')
        if status == 'REFUSED' and not reason:
            raise forms.ValidationError("Please provide a reason for refusal.")
        return self.cleaned_data

class PrivacySettingsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['workout_visibility']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5, 'maxlength': 5000}),
        }

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {'message': forms.Textarea(attrs={'rows': 5}),}

class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = ['title', 'description', 'goal_target', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }