from rest_framework import serializers
from .models import CustomUser, CoachAvailability, Message, GymInfo

# Implement REST API later

class CoachSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

class AvailabilitySerializer(serializers.ModelSerializer):
    coach = serializers.PrimaryKeyRelatedField(read_only=True)  # set automatically from request
    start = serializers.DateTimeField(source='start_time')
    end = serializers.DateTimeField(source='end_time')
    is_recurring = serializers.BooleanField()
    recurrence_group = serializers.UUIDField(read_only=True)

    class Meta:
        model = CoachAvailability
        fields = ['id', 'coach', 'start', 'end', 'is_booked', 'is_recurring', 'recurrence_group']

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'sender_name', 'recipient_name',
                  'subject', 'body', 'timestamp', 'is_read']

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.email

    def get_recipient_name(self, obj):
        return obj.recipient.get_full_name() or obj.recipient.email

class GymInfoSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = GymInfo
        fields = ['day', 'day_display', 'is_open', 'open_time', 'close_time']