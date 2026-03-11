
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CoachRequestForm
from .models import CustomUser,CoachAppointment,CoachAvailability,EquipmentBooking,EquipmentList

from .models import Article, Recipe, RecipeIngredient

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CoachRequestForm
    model = CustomUser
    list_display = ("email","role",  "is_staff", "is_active",)
    list_filter = ("email","role",  "is_staff", "is_active",)
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
            )}
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)


# added to make the admin able to view the articles and CustomUser
admin.site.register(Article)
admin.site.register(CustomUser, CustomUserAdmin)

class RecipeIngredientInline(admin.TabularInline):
    """Show ingredients directly on the Recipe admin page."""
    model = RecipeIngredient
    extra = 3  # three blank rows by default


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display  = ('title', 'author', 'difficulty', 'prep_time_minutes', 'cook_time_minutes', 'servings', 'locked', 'created_at')
    list_filter   = ('difficulty', 'locked')
    search_fields = ('title', 'author__email')
    inlines       = [RecipeIngredientInline]


@admin.register(EquipmentList)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(EquipmentBooking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'coach', 'start_time', 'end_time', 'is_cancelled')
    list_filter = ('is_cancelled', 'coach')
    search_fields = ('EquipmentBooking_name', 'coach__email')
    date_hierarchy = 'start_time'

@admin.register(CoachAvailability)
class CoachAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('coach', 'start_time', 'end_time', 'is_booked')
    list_filter = ('coach', 'is_booked')
    date_hierarchy = 'start_time'

@admin.register(CoachAppointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('member', 'coach', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'coach')
    search_fields = ('member__email', 'coach__email')
    date_hierarchy = 'start_time'


