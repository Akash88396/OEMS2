from django.contrib.auth.decorators import user_passes_test

def admin_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.role == 'admin',
        login_url='/accounts/login/',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def faculty_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.role == 'faculty',
        login_url='/accounts/login/',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def student_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.role == 'student',
        login_url='/accounts/login/',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator