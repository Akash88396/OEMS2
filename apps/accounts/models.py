from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # Define Roles
    ADMIN = 'admin'
    FACULTY = 'faculty'
    STUDENT = 'student'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (FACULTY, 'Faculty'),
        (STUDENT, 'Student'),
    ]

    # Add custom fields
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    address = models.TextField(blank=True)
    
    # Specific fields for validation
    is_approved = models.BooleanField(default=False) # For faculty/students waiting for admin approval

    def __str__(self):
        return f"{self.username} ({self.role})"