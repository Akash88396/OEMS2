from django.db import models
from django.conf import settings
from academics.models import Subject

class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    # Link to the Subject (e.g., Data Structures)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    
    # The actual question text
    text = models.TextField()
    
    # MCQ Options
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255, blank=True, null=True)
    option_d = models.CharField(max_length=255, blank=True, null=True)
    
    # Store the correct option (A, B, C, or D)
    correct_answer = models.CharField(max_length=1, help_text="Enter A, B, C, or D")
    
    # Metadata
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')

    def __str__(self):
        return f"{self.subject.code} - {self.text[:50]}..."

class Exam(models.Model):
    title = models.CharField(max_length=200, help_text="e.g., Mid-Term CS101")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    instructions = models.TextField(
        default="1. Ensure a stable internet connection.\n2. Do not switch tabs or minimize the browser.\n3. Your webcam will be monitored by AI. Looking away will result in malpractice warnings.\n4. If you refresh the page, your timer will NOT reset.",
        help_text="Instructions shown to students in the waiting lobby."
    )
    # The faculty member who created the exam
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'faculty'}
    )
    
    # Link to the Question Bank (Many-to-Many allows selecting multiple questions)
    questions = models.ManyToManyField(Question, through='ExamQuestion', related_name='exams')
    # Scheduling and Rules
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(help_text="Total time allowed in minutes")
    
    # Security and Evaluation
    proctoring_enabled = models.BooleanField(default=True, help_text="Enable AI Camera Surveillance")
    passing_marks = models.PositiveIntegerField()

    # Notice: 'total_marks' field is REMOVED! It is now an auto-calculated property.
    @property
    def total_marks(self):
        # Automatically sums up the marks of all questions assigned to this exam
        total = sum(item.marks for item in ExamQuestion.objects.filter(exam=self))
        return total if total else 0
    
    def __str__(self):
        return self.title

class ExamQuestion(models.Model):
    """The 'Through' model that links an Exam, a Question, and the Marks for that specific combination."""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    # NEW: Marks are now defined per question, per exam!
    marks = models.PositiveIntegerField(default=1)

    class Meta:
        # Prevents adding the exact same question to the exact same exam twice
        unique_together = ('exam', 'question')

    def __str__(self):
        return f"{self.exam.title} - {self.question.id} ({self.marks} Marks)"
    
class StudentExam(models.Model):
    """Tracks a student's attempt for a specific exam"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'student'}
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='in_progress') # 'in_progress' or 'submitted'
    
    # We will use this in Phase 5 for the AI Camera Surveillance
    proctoring_warnings = models.IntegerField(default=0) 

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"

class StudentResponse(models.Model):
    """Tracks the answer selected for a specific question"""
    student_exam = models.ForeignKey(StudentExam, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    # The option the student clicked (A, B, C, or D)
    selected_option = models.CharField(max_length=1, blank=True, null=True) 

    def __str__(self):
        return f"Response to {self.question.id} by {self.student_exam.student.username}"
    

