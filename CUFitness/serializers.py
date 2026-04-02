from rest_framework import serializers
from .models import CustomUser, CoachReview

# Serializer for user data
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'profile_picture', 'is_active'
        ]
        read_only_fields = ['id', 'email', 'role']

    # Returns the user's full name
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


# Serializer for coach reviews
class CoachReviewSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()
    coach_name = serializers.SerializerMethodField()
    appointment_date = serializers.SerializerMethodField()

    class Meta:
        model = CoachReview
        fields = [
            'id', 'coach', 'member', 'member_name', 'coach_name',
            'appointment', 'appointment_date', 'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'member', 'coach', 'appointment']

    # Returns the reviewing member's full name
    def get_member_name(self, obj):
        return f"{obj.member.first_name} {obj.member.last_name}".strip() or obj.member.email

    # Returns the reviewed coach's full name
    def get_coach_name(self, obj):
        return f"{obj.coach.first_name} {obj.coach.last_name}".strip() or obj.coach.email

    # Returns the appointment date and time in a readable format
    def get_appointment_date(self, obj):
        return obj.appointment.start_time.strftime("%Y-%m-%d %H:%M")