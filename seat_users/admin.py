from django.contrib import admin
from .models import Billing, Course, User, AdoptionAdmin

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price', 'payment_status', 'created_at', 'is_verified')
    list_filter = ('payment_status', 'is_verified')
    search_fields = ('user__full_name', 'user__email')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'branch', 'city', 'institute_name', 'total_seats', 'left_seats', 'price_per_seat')
    list_filter = ('course_name', 'city', 'institute_type')
    search_fields = ('course_name', 'branch', 'institute_name', 'city')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone_number', 'company_name', 'role', 'adopted_students')
    list_filter = ('role', 'created_at')
    search_fields = ('full_name', 'email', 'phone_number', 'company_name')

@admin.register(AdoptionAdmin)
class AdoptionAdminAdmin(admin.ModelAdmin):
    list_display = ('username', 'created_at')
    search_fields = ('username',)
