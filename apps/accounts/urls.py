from django.urls import path
from .views import CustomLoginView, admin_dashboard, faculty_dashboard, student_dashboard
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    # Dashboards
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/faculty/', faculty_dashboard, name='faculty_dashboard'),
    path('dashboard/student/', student_dashboard, name='student_dashboard'),
]