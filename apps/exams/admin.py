from django.contrib import admin
from .models import Question, Exam, ExamQuestion

class ExamQuestionInline(admin.TabularInline):
    model = ExamQuestion
    extra = 1 # Shows one blank row to add a new question

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'subject', 'difficulty')
    list_filter = ('subject', 'difficulty')
    # search_fields = ('text',)

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'start_time', 'duration_minutes', 'proctoring_enabled')
    list_filter = ('subject', 'proctoring_enabled')
    inlines = [ExamQuestionInline]