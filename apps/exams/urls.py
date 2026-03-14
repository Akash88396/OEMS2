from django.urls import path
from .views import exam_console, save_answer,submit_exam, exam_result, log_warning, admin_result_viewer, admin_exam_detail, add_question, create_exam, exam_lobby, question_bank, bulk_upload_questions ,ai_question_generator

urlpatterns = [
    path('lobby/<int:exam_id>/', exam_lobby, name='exam_lobby'),
    path('take/<int:exam_id>/', exam_console, name='exam_console'),
    path('api/save_answer/', save_answer, name='save_answer'), # NEW API ENDPOINT
    path('api/submit_exam/', submit_exam, name='submit_exam'), # NEW
    path('result/<int:student_exam_id>/', exam_result, name='exam_result'), # NEW
    path('api/log_warning/', log_warning, name='log_warning'),
    path('admin/results/', admin_result_viewer, name='admin_results'),
    path('admin/results/<int:student_exam_id>/', admin_exam_detail, name='admin_exam_detail'),
    path('faculty/add-question/', add_question, name='add_question'),
    path('faculty/create-exam/', create_exam, name='create_exam'),
    path('faculty/question-bank/', question_bank, name='question_bank'),
    path('faculty/bulk-upload/', bulk_upload_questions, name='bulk_upload_questions'),
    path('faculty/ai-generator/', ai_question_generator, name='ai_question_generator'),
]