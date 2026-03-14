from django.contrib import admin
from .models import Course, Subject

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_years')
    search_fields = ('name',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'course', 'faculty')
    list_filter = ('course', 'faculty')
    search_fields = ('name', 'code')