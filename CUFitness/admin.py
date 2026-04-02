# Django
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Local
from .forms import CustomUserCreationForm
from .models import (
    Article, Challenge, ChallengeParticipation, CoachAppointment, CoachAvailability,
    CoachReview, CustomUser, EquipmentList, Exercise, GymInfo, Recipe, RecipeIngredient,
    WorkoutPlan, WorkoutPlanExercise, ContactMessage
)

# Custom user admin with role-based permissions
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    # form = CoachRequestForm  # not used
    model = CustomUser
    list_display = ("email", "role", "is_staff", "is_active")
    list_filter = ("email", "role", "is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "membership", "role")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "password1", "password2", "is_staff",
                "is_active", "groups", "user_permissions", "role"
            )
        }),
    )
    search_fields = ("email",)
    ordering = ("email",)


# added to make the admin able to view the articles and CustomUser
admin.site.register(CustomUser, CustomUserAdmin)

# Article management in admin
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'locked', 'created_at')
    list_filter = ('created_at', 'locked')
    search_fields = ('title', 'author__email')

# Inline form for recipe ingredients
class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 3  # three blank rows by default

# Recipe management with inline ingredients
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'difficulty', 'prep_time_minutes', 'cook_time_minutes', 'servings', 'locked', 'created_at')
    list_filter = ('difficulty', 'locked')
    search_fields = ('title', 'author__email')
    inlines = [RecipeIngredientInline]

# Equipment list management
@admin.register(EquipmentList)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

# Coach availability slots
@admin.register(CoachAvailability)
class CoachAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('coach', 'start_time', 'end_time', 'is_booked')
    list_filter = ('coach', 'is_booked')
    date_hierarchy = 'start_time'

# Coach appointments
@admin.register(CoachAppointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('member', 'coach', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'coach')
    search_fields = ('member__email', 'coach__email')
    date_hierarchy = 'start_time'

# Gym operating hours
@admin.register(GymInfo)
class GymInfoAdmin(admin.ModelAdmin):
    list_display = ('day', 'is_open', 'is_open_24h', 'open_time', 'close_time')
    list_editable = ('is_open', 'is_open_24h', 'open_time', 'close_time')
    ordering = ('day',)

# Fitness challenges
@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'goal_target', 'start_date', 'end_date', 'created_by', 'created_at')
    list_filter = ('start_date', 'end_date', 'created_by')
    search_fields = ('title', 'description', 'created_by__email')
    ordering = ('-created_at',)

# User participation in challenges
@admin.register(ChallengeParticipation)
class ChallengeParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'progress', 'joined_at', 'progress_percentage_display')
    list_filter = ('challenge', 'joined_at')
    search_fields = ('user__email', 'challenge__title')
    ordering = ('-joined_at',)

    def progress_percentage_display(self, obj):
        return f"{obj.progress_percentage()}%"
    progress_percentage_display.short_description = "Progress (%)"

# Coach reviews
@admin.register(CoachReview)
class CoachReviewAdmin(admin.ModelAdmin):
    list_display = ('coach', 'member', 'rating', 'comment_preview', 'appointment', 'created_at')
    list_filter = ('rating', 'created_at', 'coach')
    search_fields = ('coach__email', 'member__email', 'comment')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    def comment_preview(self, obj):
        return obj.comment[:50] + '…' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment (preview)'

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_read']
    list_filter = ['is_read']
    search_fields = ['name', 'email', 'subject']