# Django
from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.forms import inlineformset_factory

# Local
from .models import (
    Article, Challenge, CoachReview,
    ContactMessage, CustomUser, Message, Recipe, RecipeIngredient
)

# Registration form for new members
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", 'phone_number', 'date_of_birth', 'address', 'membership')
        widgets = {
            'membership': forms.Select(attrs={'class': 'styled-select'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

# Change email address with uniqueness check
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

# Change password uses Django's built‑in validation
class UpdatePasswordForm(PasswordChangeForm):
    pass

# Upload or update profile picture
class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_picture']

# Create or edit an article (author set manually in view)
class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'description', 'body', 'locked']
        exclude = ["author"]
        widgets = {}

# Create or edit a recipe
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

# Inline formset for recipe ingredients (3 empty rows by default)
IngredientFormSet = inlineformset_factory(
    parent_model=Recipe,
    model=RecipeIngredient,
    fields=['name', 'quantity', 'unit', 'notes'],
    extra=3,
    can_delete=True,
)

# User privacy settings (workout visibility)
class PrivacySettingsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['workout_visibility']

# Staff creates/edits a fitness challenge
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

# Member submits a review for a completed appointment
class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [(i, f"{i} star{'s' if i > 1 else ''}") for i in range(1, 6)]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Rating'
    )

    class Meta:
        model = CoachReview
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': 500,
                'placeholder': 'Share your experience (max 500 characters)',
                'class': 'form-control'
            }),
        }
        labels = {
            'rating': 'Your star rating',
            'comment': 'Your review (optional)',
        }
        help_texts = {
            'comment': 'Maximum 500 characters.',
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        try:
            rating_int = int(rating)
            if rating_int not in range(1, 6):
                raise forms.ValidationError('Rating must be between 1 and 5.')
            return rating_int
        except (TypeError, ValueError):
            raise forms.ValidationError('Invalid rating value.')







# =================================================================================================================
# ============Potentially Not used Functions===========
# # Coach request notifications
# class CoachRequestForm(forms.ModelForm):
#     class Meta:
#         model = CustomUser
#         fields = []
#
# # Coach accepts/refuses a pending appointment
# class AppointmentResponseForm(forms.ModelForm):
#     class Meta:
#         model = CoachAppointment
#         fields = ['status', 'refusal_reason']
#         widgets = {
#             'refusal_reason': forms.Textarea(attrs={'rows': 3}),
#         }
#
#     def clean(self):
#         status = self.cleaned_data.get('status')
#         reason = self.cleaned_data.get('refusal_reason')
#         if status == 'REFUSED' and not reason:
#             raise forms.ValidationError("Please provide a reason for refusal.")
#         return self.cleaned_data
#
# # Send a message (member to coach)
# class MessageForm(forms.ModelForm):
#     class Meta:
#         model = Message
#         fields = ['subject', 'body']
#         widgets = {
#             'body': forms.Textarea(attrs={'rows': 5, 'maxlength': 5000}),
#         }
#
# # Coach availability slot (used in legacy manage_availability view)
# class CoachAvailabilityForm(forms.ModelForm):
#     class Meta:
#         model = CoachAvailability
#         fields = ['start_time', 'end_time', 'is_recurring']
#
#     def __init__(self, *args, **kwargs):
#         self.coach = kwargs.pop('coach', None)
#         self.selected_date = kwargs.pop('selected_date', None)
#         super().__init__(*args, **kwargs)
#
#     def clean(self):
#         cleaned = super().clean()
#         start = cleaned.get('start_time')
#         end = cleaned.get('end_time')
#         if start and end:
#             # Must be same day and exactly one hour
#             if start.date() != end.date():
#                 raise ValidationError("Start and end must be on the same day.")
#             if (end - start) != timedelta(hours=1):
#                 raise ValidationError("Slot must be exactly one hour.")
#             # Check against gym hours
#             weekday = start.weekday()
#             try:
#                 gym_day = GymInfo.objects.get(day=weekday)
#                 if not gym_day.is_open:
#                     raise ValidationError("Gym is closed on this day.")
#                 if start.time() < gym_day.open_time or end.time() > gym_day.close_time:
#                     raise ValidationError("Slot must be within gym operating hours.")
#             except GymInfo.DoesNotExist:
#                 raise ValidationError("Gym hours not configured for this day.")
#         return cleaned
#
#
# # Member requests an appointment (not actively used – handled by API)
# class AppointmentRequestForm(forms.ModelForm):
#     class Meta:
#         model = CoachAppointment
#         fields = ['start_time', 'end_time']
#         widgets = {
#             'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#             'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#         }
#
#     def __init__(self, *args, **kwargs):
#         self.coach = kwargs.pop('coach', None)
#         super().__init__(*args, **kwargs)
#
#     def clean(self):
#         cleaned_data = super().clean()
#         # Validation is handled in the view (API provides only available slots)
#         return cleaned_data
