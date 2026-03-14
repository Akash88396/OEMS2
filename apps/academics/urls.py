from academics.views import manage_subjects
from django.urls import path
urlpatterns = [
    # ... your existing routes ...
    path('admin-dashboard/subjects/', manage_subjects, name='manage_subjects'),
]