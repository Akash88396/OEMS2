from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    # Fields to display in the list view (the table of users)
    list_display = ['username', 'email', 'role', 'is_approved', 'is_staff']
    
    # Fields to filter by on the right sidebar
    list_filter = ['role', 'is_approved', 'is_staff']
    
    # Organize fields in the "Edit User" form
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'is_approved', 'profile_picture', 'address')}),
    )
    
    # Organize fields in the "Add User" form
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role', 'is_approved', 'profile_picture', 'address')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)