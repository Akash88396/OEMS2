from django.db import models
from django.conf import settings

class Course(models.Model):
    name = models.CharField(max_length=150, unique=True, help_text="e.g., B.Tech Computer Science")
    duration_years = models.PositiveIntegerField(default=4)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True, help_text="e.g., CS101")
    
    # Link subject to a specific course
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    
    # Link subject to a faculty member. Notice the limit_choices_to!
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'faculty'},
        related_name='assigned_subjects'
    )

    def __str__(self):
        return f"{self.name} ({self.code})"