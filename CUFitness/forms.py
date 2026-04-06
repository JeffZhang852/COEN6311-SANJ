# Django
from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.forms import inlineformset_factory

# Local
from .models import (
    Article, Challenge, CoachReview,
    ContactMessage, CustomUser, Exercise, Message, Recipe, RecipeIngredient,
    WorkoutPlan
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

# Create or edit an exercise
class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = [
            'title', 'description', 'instructions',
            'muscle_group', 'difficulty', 'goal', 'equipment',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'instructions': forms.Textarea(attrs={'rows': 6}),
            'equipment': forms.CheckboxSelectMultiple(),
        }

# Create or edit a workout plan (author set manually in view)
class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ['title', 'description', 'body', 'difficulty', 'duration_minutes', 'goal', 'locked']
        exclude = ['author']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'body': forms.Textarea(attrs={'rows': 6}),
        }

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
