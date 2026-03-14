from django import forms
from .models import Question, Exam, ExamQuestion
from academics.models import Subject

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        # REMOVED 'marks'
        fields = ['subject', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'difficulty']

    def __init__(self, faculty_user, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        
        # Security: Only show subjects assigned to this specific faculty member
        self.fields['subject'].queryset = Subject.objects.filter(faculty=faculty_user)
        
        # Add Tailwind CSS classes to all form fields dynamically
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition'
            
        # Customize specific widgets if needed
        self.fields['text'].widget.attrs['rows'] = 3
        self.fields['text'].widget.attrs['placeholder'] = 'Type your question here...'


class ExamForm(forms.ModelForm):
    # We must explicitly define this field because Django ModelForms cannot auto-generate 
    # a field for a ManyToMany relationship that uses a custom 'through' model.
    

    class Meta:
        model = Exam
        # REMOVED 'total_marks' and 'questions' from here
        fields = ['title', 'subject', 'start_time', 'end_time', 'duration_minutes', 'passing_marks', 'proctoring_enabled','instructions']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, faculty_user, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        
        # Security: Only show subjects assigned to this faculty
        self.fields['subject'].queryset = Subject.objects.filter(faculty=faculty_user)
        
        # Security: Update our manually defined questions field
        
        
        self.fields['instructions'].widget.attrs['rows'] = 4
        
        # Add Tailwind CSS classes
        for field_name, field in self.fields.items():
            if field_name == 'proctoring_enabled':
                field.widget.attrs['class'] = 'w-5 h-5 text-teal-600 border-gray-300 rounded focus:ring-teal-500 cursor-pointer'
            else:
                field.widget.attrs['class'] = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition bg-white'