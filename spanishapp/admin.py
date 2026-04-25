from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    LanguageLevel, CourseType, StudentProfile,
    TeacherProfile, Status, TimeSlot, Booking
)

admin.site.register(LanguageLevel)
admin.site.register(CourseType)
admin.site.register(Status)
admin.site.register(TimeSlot)
admin.site.register(Booking)

@admin.register(StudentProfile)
class StudentAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Student Info", {"fields": ("photo", "date_of_birth", "country_of_birth", "country_of_residence", "level")}),
    )

@admin.register(TeacherProfile)
class TeacherAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Teacher Info", {"fields": ("photo", "date_of_birth", "biography", "country_of_birth", "country_of_residence", "courses")}),
    )
    