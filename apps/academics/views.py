from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import admin_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Subject, Course

User = get_user_model()

@login_required
@admin_required
def manage_subjects(request):
    course_q = request.GET.get('course_q', '')
    subject_q = request.GET.get('subject_q', '')
    active_tab = request.GET.get('tab', 'courses')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Action A: Create Course (UPDATED TO MATCH YOUR MODEL)
        if action == 'create_course':
            name = request.POST.get('name')
            duration_years = request.POST.get('duration_years', 4)
            description = request.POST.get('description', '')
            
            if name:
                Course.objects.create(name=name, duration_years=duration_years, description=description)
                messages.success(request, f'Course "{name}" created successfully!')
            return redirect('/admin-dashboard/subjects/?tab=courses')
            
        # Action B: Create Subject
        elif action == 'create_subject':
            name = request.POST.get('name')
            code = request.POST.get('code')
            course_id = request.POST.get('course_id')
            faculty_id = request.POST.get('faculty_id')
            
            if name and code:
                course = Course.objects.get(id=course_id) if course_id else None
                faculty = User.objects.get(id=faculty_id) if faculty_id else None
                
                Subject.objects.create(name=name, code=code, course=course, faculty=faculty)
                messages.success(request, f'Subject "{code}" created successfully!')
            return redirect('/admin-dashboard/subjects/?tab=subjects')

    # Fetch Data & Apply Search Filters
    courses = Course.objects.all().order_by('name')
    if course_q:
        # Only search by name, since Course doesn't have a 'code'
        courses = courses.filter(name__icontains=course_q)

    subjects = Subject.objects.all().select_related('faculty', 'course').order_by('code')
    if subject_q:
        subjects = subjects.filter(Q(name__icontains=subject_q) | Q(code__icontains=subject_q))

    faculty_list = User.objects.filter(role='faculty', is_active=True)
    all_courses = Course.objects.all()

    context = {
        'courses': courses,
        'subjects': subjects,
        'faculty_list': faculty_list,
        'all_courses': all_courses,
        'course_q': course_q,
        'subject_q': subject_q,
        'active_tab': active_tab,
    }
    return render(request, 'academics/manage_subjects.html', context)
