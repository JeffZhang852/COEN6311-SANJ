# registration form
#django handles the backend database

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms


#   --------- OLD -- NOT USED---------
'''
class SignUpForm(UserCreationForm):
    # bootstrap form
    email = forms.EmailField(label="",
                             widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    first_name = forms.CharField(label="", max_length=100,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(label="", max_length=100,
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'User Name'
        self.fields['username'].label = ''
        self.fields[
            'username'].help_text = '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'

        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password1'].label = ''
        self.fields[
            'password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>'

        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
        self.fields['password2'].label = ''
        self.fields[
            'password2'].help_text = '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'
'''

####################################################
# new user model

from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser,CoachAppointment,CoachAvailability,Equipment_Booking


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", 'membership')
        # dropdown membership selection
        widgets = {
            'membership': forms.Select(attrs={
                'class': 'styled-select'})
        }

# Replaced, unless needed otherwise
# class CustomUserChangeForm(UserChangeForm):
#
#     class Meta:
#         model = CustomUser
#         fields = ("email",)



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