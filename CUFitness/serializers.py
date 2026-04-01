# CUFitness/serializers.py

from rest_framework import serializers
from .models import (
    CustomUser, CoachAvailability, CoachAppointment, Article,
    Recipe, RecipeIngredient, WorkoutPlan, WorkoutPlanExercise,
    Exercise, Message, Challenge, ChallengeParticipation, GymInfo
)


# =============================================================================
# Helper / Base Serializers
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'membership', 'profile_picture', 'phone_number',
            'date_of_birth', 'address', 'workout_visibility',
            'coach_request_status', 'auto_accept_appointments',
            'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'role']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class CoachAvailabilitySerializer(serializers.ModelSerializer):
    coach = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CoachAvailability
        fields = [
            'id', 'coach', 'start_time', 'end_time', 'is_booked',
            'is_recurring', 'recurrence_group'
        ]


class CoachAppointmentSerializer(serializers.ModelSerializer):
    coach = UserSerializer(read_only=True)
    member = UserSerializer(read_only=True)
    availability = CoachAvailabilitySerializer(read_only=True)

    class Meta:
        model = CoachAppointment
        fields = [
            'id', 'coach', 'member', 'availability', 'start_time', 'end_time',
            'status', 'refusal_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


# =============================================================================
# Articles, Recipes, Workouts, Exercises
# =============================================================================

class ArticleSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'description', 'body', 'locked',
            'author', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'quantity', 'unit', 'unit_other', 'notes']


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    dietary_restrictions = serializers.ListField(
        child=serializers.CharField(),
        source='dietary_restrictions',
        read_only=True
    )
    total_time_minutes = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'description', 'locked', 'prep_time_minutes',
            'cook_time_minutes', 'servings', 'difficulty', 'instructions',
            'calories_per_serving', 'dietary_restrictions', 'author',
            'created_at', 'updated_at', 'ingredients', 'total_time_minutes'
        ]
        read_only_fields = ['created_at', 'updated_at']


class WorkoutPlanExerciseSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    exercise_id = serializers.PrimaryKeyRelatedField(source='exercise', read_only=True)

    class Meta:
        model = WorkoutPlanExercise
        fields = [
            'id', 'exercise_id', 'exercise_title', 'sets', 'reps',
            'rest_seconds', 'order', 'notes'
        ]


class WorkoutPlanSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    exercises = WorkoutPlanExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutPlan
        fields = [
            'id', 'title', 'description', 'body', 'locked', 'difficulty',
            'duration_minutes', 'goal', 'author', 'created_at', 'updated_at',
            'exercises'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ExerciseSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    equipment = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'id', 'title', 'description', 'instructions', 'muscle_group',
            'difficulty', 'goal', 'equipment', 'created_by', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


# =============================================================================
# Messaging
# =============================================================================

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'recipient', 'sender_name', 'recipient_name',
            'subject', 'body', 'timestamp', 'is_read'
        ]
        read_only_fields = ['timestamp', 'is_read']

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.email

    def get_recipient_name(self, obj):
        return obj.recipient.get_full_name() or obj.recipient.email


# =============================================================================
# Challenges
# =============================================================================

class ChallengeSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Challenge
        fields = [
            'id', 'title', 'description', 'goal_target', 'start_date',
            'end_date', 'created_by', 'created_at'
        ]
        read_only_fields = ['created_at']


class ChallengeParticipationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    challenge = ChallengeSerializer(read_only=True)
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = ChallengeParticipation
        fields = [
            'id', 'user', 'challenge', 'progress', 'joined_at',
            'progress_percentage'
        ]
        read_only_fields = ['joined_at']

    def get_progress_percentage(self, obj):
        return obj.progress_percentage()


# =============================================================================
# Gym Info
# =============================================================================

class GymInfoSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = GymInfo
        fields = ['day', 'day_display', 'is_open', 'open_time', 'close_time']