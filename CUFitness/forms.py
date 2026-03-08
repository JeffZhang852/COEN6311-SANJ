

from django import forms

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser,CoachAppointment,CoachAvailability,EquipmentBooking
from .models import Articles

from django.contrib.auth.forms import PasswordChangeForm


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", 'membership')
        # dropdown membership selection
        widgets = {
            'membership': forms.Select(attrs={
                'class': 'styled-select'})
        }


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Articles
        fields = ['title','description', 'body', 'locked']
        exclude = ["author"] # we set it manually
        widgets = {}

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



class CoachAvailabilityForm(forms.ModelForm):
    class Meta:
        model = CoachAvailability
        fields = ['start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

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
        if status == 'refused' and not reason:
            raise forms.ValidationError("Please provide a reason for refusal.")
        return self.cleaned_data

class PrivacySettingsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['workout_visibility']





# Replaced, unless needed otherwise
# class CustomUserChangeForm(UserChangeForm):
#
#     class Meta:
#         model = CustomUser
#         fields = ("email",)
