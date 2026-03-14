from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator

from django.utils import timezone
from django.contrib import messages
import google.generativeai as genai
from django.conf import settings

import json
from datetime import timedelta
import csv
import io
import random


from apps.accounts.decorators import admin_required,  faculty_required, student_required

from exams.models import Exam, StudentExam, StudentResponse, Question, ExamQuestion
from academics.models import Subject

from exams.forms import QuestionForm, ExamForm

@login_required
@student_required
def exam_lobby(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    now = timezone.now()
    
    # Check if student already submitted
    if StudentExam.objects.filter(student=request.user, exam=exam, status='submitted').exists():
        messages.warning(request, "You have already completed this exam.")
        return redirect('student_dashboard')

    # Calculate lobby window (opens 20 mins before start)
    lobby_open_time = exam.start_time - timedelta(minutes=20)
    
    if now < lobby_open_time:
        messages.error(request, f"The lobby for this exam opens at {lobby_open_time.strftime('%I:%M %p')}.")
        return redirect('student_dashboard')

    # Is the exam strictly active right now?
    exam_active = exam.start_time <= now <= exam.end_time

    context = {
        'exam': exam,
        'exam_active': exam_active,
    }
    return render(request, 'exams/exam_lobby.html', context)




@login_required
def exam_console(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    now = timezone.now()

    # Security Check: Ensure exam is currently active
    if now < exam.start_time or now > exam.end_time:
        messages.error(request, "This exam is currently not active.")
        return redirect('student_dashboard')

    student_exam, created = StudentExam.objects.get_or_create(
        student=request.user,
        exam=exam,
        defaults={'status': 'in_progress'}
    )
    
    if student_exam.status == 'submitted':
        return render(request, 'exams/exam_submitted.html', {'student_exam': student_exam})

    # --- SERVER-SIDE TIMER LOGIC (IMMUNE TO REFRESH) ---
    # Expected end time is when they started + the allowed duration
    expected_end_time = student_exam.started_at + timedelta(minutes=exam.duration_minutes)
    
    # Calculate seconds left
    time_left = (expected_end_time - now).total_seconds()
    
    # If time is already up, auto-submit them immediately
    if time_left <= 0:
        student_exam.status = 'submitted'
        student_exam.completed_at = now
        student_exam.save()
        return redirect('exam_result', student_exam_id=student_exam.id)

    questions = exam.questions.all()
    saved_responses = StudentResponse.objects.filter(student_exam=student_exam)
    answered_dict = {resp.question.id: resp.selected_option for resp in saved_responses}

    # --- UPGRADED: Option Shuffling Logic ---
    for q in questions:
        q.selected_option = answered_dict.get(q.id)
        
        # 1. Package the original options
        raw_options = [
            {'orig': 'A', 'text': q.option_a},
            {'orig': 'B', 'text': q.option_b},
        ]
        if q.option_c: raw_options.append({'orig': 'C', 'text': q.option_c})
        if q.option_d: raw_options.append({'orig': 'D', 'text': q.option_d})
        
        # 2. Shuffle deterministically! (Same student + Same question = Same shuffle order)
        seed = f"{student_exam.id}_{q.id}"
        random.Random(seed).shuffle(raw_options)
        
        # 3. Assign new display letters (A, B, C, D) purely for visuals
        for index, opt in enumerate(raw_options):
            opt['display'] = chr(65 + index) # 65 is 'A' in ASCII
            
        q.shuffled_options = raw_options

    context = {
        'exam': exam,
        'questions': questions,
        'student_exam': student_exam,
        'answered_dict': answered_dict,
        'time_left_seconds': int(time_left), # Pass the exact remaining seconds to JS!
    }
    return render(request, 'exams/exam_console.html', context)

# 3. The API to save answers in real-time
@login_required
@csrf_exempt # In production, pass the CSRF token in JS instead of exempting
def save_answer(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        student_exam_id = data.get('student_exam_id')
        question_id = data.get('question_id')
        selected_option = data.get('selected_option')

        student_exam = get_object_or_404(StudentExam, id=student_exam_id, student=request.user)
        question = get_object_or_404(Question, id=question_id)

        # Update or create the response
        response, created = StudentResponse.objects.update_or_create(
            student_exam=student_exam,
            question=question,
            defaults={'selected_option': selected_option}
        )
        
        return JsonResponse({'status': 'success', 'message': 'Answer saved'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
@csrf_exempt
def submit_exam(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        student_exam_id = data.get('student_exam_id')
        
        # Fetch the student's exam session
        student_exam = get_object_or_404(StudentExam, id=student_exam_id, student=request.user)

        # Prevent double submission
        if student_exam.status == 'submitted':
            return JsonResponse({'status': 'error', 'message': 'Exam already submitted'})

        # Auto-Grader Logic: Calculate the total score
        # total_score = 0
        # responses = student_exam.responses.all()
        # for response in responses:
        #     if response.selected_option == response.question.correct_answer:
        #         total_score += response.question.marks
        total_score = 0
        responses = student_exam.responses.all()
        for response in responses:
            if response.selected_option == response.question.correct_answer:
                # Fetch the specific marks for THIS question in THIS exam
                exam_question = ExamQuestion.objects.get(exam=student_exam.exam, question=response.question)
                total_score += exam_question.marks

        # Update the exam session to 'submitted'
        student_exam.score = total_score
        student_exam.status = 'submitted'
        student_exam.completed_at = timezone.now()
        student_exam.save()

        # Send back the URL where the JS should redirect the user
        redirect_url = f'/exams/result/{student_exam.id}/'
        return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
        
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def exam_result(request, student_exam_id):
    # This view just shows the final score page
    student_exam = get_object_or_404(StudentExam, id=student_exam_id, student=request.user)
    return render(request, 'exams/exam_submitted.html', {'student_exam': student_exam})


@login_required
@csrf_exempt
def log_warning(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        student_exam_id = data.get('student_exam_id')
        
        # Fetch the session
        student_exam = get_object_or_404(StudentExam, id=student_exam_id, student=request.user)
        
        # Increment the warning count
        student_exam.proctoring_warnings += 1
        student_exam.save()
        
        return JsonResponse({
            'status': 'success', 
            'warnings': student_exam.proctoring_warnings
        })
    return JsonResponse({'status': 'error'}, status=400)



@login_required
@admin_required
def admin_result_viewer(request):
    # Fetch all completed exams and order them by most recently completed
    # We use select_related to optimize database queries for foreign keys
    completed_exams = StudentExam.objects.filter(status='submitted').select_related('student', 'exam').order_by('-completed_at')
    
    context = {
        'results': completed_exams
    }
    return render(request, 'exams/admin_results.html', context)


@login_required
@admin_required
def admin_exam_detail(request, student_exam_id):
    # Fetch the specific exam attempt
    student_exam = get_object_or_404(StudentExam, id=student_exam_id)
    
    # Fetch all questions for this exam
    questions = student_exam.exam.questions.all()
    
    # Fetch the student's responses and map them by question ID for easy lookup
    responses = {resp.question.id: resp for resp in student_exam.responses.all()}
    
    # Build a detailed list for the template
    detailed_answers = []
    for q in questions:
        resp = responses.get(q.id)
        selected = resp.selected_option if resp else None
        is_correct = (selected == q.correct_answer) if resp else False
        
        detailed_answers.append({
            'question': q,
            'selected': selected,
            'is_correct': is_correct
        })

    # Calculate percentage
    percentage = 0
    if student_exam.exam.total_marks > 0:
        percentage = round((student_exam.score / student_exam.exam.total_marks) * 100, 2)

    context = {
        'student_exam': student_exam,
        'detailed_answers': detailed_answers,
        'percentage': percentage,
    }
    return render(request, 'exams/admin_exam_detail.html', context)


@login_required
@faculty_required
def add_question(request):
    if request.method == 'POST':
        # Pass the logged-in user to the form to filter subjects
        form = QuestionForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question successfully added to the Question Bank!')
            return redirect('faculty_dashboard')
        else:
            messages.error(request, 'There was an error saving the question. Please check the form.')
    else:
        form = QuestionForm(request.user)

    context = {
        'form': form,
    }
    return render(request, 'exams/add_question.html', context)


@login_required
@faculty_required
def create_exam(request):
    # Fetch all questions belonging to this faculty to display in the list
    available_questions = Question.objects.filter(subject__faculty=request.user).select_related('subject')

    if request.method == 'POST':
        form = ExamForm(request.user, request.POST)
        
        # 1. Manually extract the checked questions from the frontend HTML
        selected_q_ids = request.POST.getlist('selected_questions')
        
        if not selected_q_ids:
            messages.error(request, 'You must select at least one question for the exam.')
            return render(request, 'exams/create_exam.html', {'form': form, 'available_questions': available_questions})

        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            
            # 2. Loop through the checked questions and save their specific marks
            for q_id in selected_q_ids:
                # Get the marks typed into the input field (defaults to 1 if empty)
                marks = request.POST.get(f'marks_{q_id}', 1)
                question = Question.objects.get(id=q_id)
                
                # Create the Through Model relationship!
                ExamQuestion.objects.create(exam=exam, question=question, marks=marks)
            
            messages.success(request, 'Exam scheduled successfully!')
            return redirect('faculty_dashboard')
        else:
            messages.error(request, 'Error creating exam. Please check the fields.')
    else:
        form = ExamForm(request.user)

    context = {
        'form': form,
        'available_questions': available_questions, # Pass questions to template
    }
    return render(request, 'exams/create_exam.html', context)

#  Question Bank Feature of Faculty
@login_required
@faculty_required
def question_bank(request):
    # Fetch subjects assigned to this faculty, and prefetch their questions
    subjects = Subject.objects.filter(faculty=request.user).prefetch_related('questions')

    context = {
        'subjects': subjects,
    }
    return render(request, 'exams/question_bank.html', context)

@login_required
@faculty_required
def question_bank(request):
    # 1. Start with a base query of all questions for this faculty
    # Using select_related('subject') ensures we don't hit the DB again when displaying the subject code
    question_list = Question.objects.filter(subject__faculty=request.user).select_related('subject').order_by('-id')

    # 2. Check if the faculty is filtering by a specific subject
    subject_filter = request.GET.get('subject')
    if subject_filter:
        question_list = question_list.filter(subject__id=subject_filter)

    # 3. Paginate the results (10 questions per page)
    paginator = Paginator(question_list, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 4. Fetch subjects for the dropdown filter
    subjects = Subject.objects.filter(faculty=request.user)

    context = {
        'page_obj': page_obj,
        'subjects': subjects,
        'current_subject': subject_filter,
    }
    return render(request, 'exams/question_bank.html', context)

# Adding Multiple questions at once through csv files
@login_required
@faculty_required
def bulk_upload_questions(request):
    # Fetch subjects so the faculty can choose where these questions go
    subjects = Subject.objects.filter(faculty=request.user)

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        csv_file = request.FILES.get('file')

        if not subject_id or not csv_file:
            messages.error(request, 'Please select a subject and upload a file.')
            return redirect('bulk_upload_questions')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Invalid file format. Please upload a .csv file.')
            return redirect('bulk_upload_questions')

        try:
            subject = Subject.objects.get(id=subject_id, faculty=request.user)
            
            # Read and decode the CSV file
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            
            # Skip the header row
            next(io_string)
            
            questions_to_create = []
            for row in csv.reader(io_string, delimiter=',', quotechar='"'):
                # We expect 7 columns: Text, Opt A, Opt B, Opt C, Opt D, Correct Ans, Difficulty
                if len(row) >= 7:
                    questions_to_create.append(Question(
                        subject=subject,
                        text=row[0].strip(),
                        option_a=row[1].strip(),
                        option_b=row[2].strip(),
                        option_c=row[3].strip() if row[3].strip() else None,
                        option_d=row[4].strip() if row[4].strip() else None,
                        correct_answer=row[5].strip().upper(),
                        difficulty=row[6].strip().lower()
                    ))
            
            # Save all questions to the database in one single, fast query
            Question.objects.bulk_create(questions_to_create)
            
            messages.success(request, f'Successfully imported {len(questions_to_create)} questions!')
            return redirect('question_bank')
            
        except Exception as e:
            messages.error(request, f'Error reading file. Please check the format. Details: {str(e)}')
            return redirect('bulk_upload_questions')

    context = {
        'subjects': subjects,
    }
    return render(request, 'exams/bulk_upload.html', context)


# Google API Keys :

@login_required
@faculty_required
def ai_question_generator(request):
    subjects = Subject.objects.filter(faculty=request.user)

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        topic = request.POST.get('topic')
        difficulty = request.POST.get('difficulty')
        num_questions = int(request.POST.get('num_questions', 5))

        if not subject_id or not topic:
            messages.error(request, 'Please provide a subject and a topic.')
            return redirect('ai_question_generator')

        try:
            subject = Subject.objects.get(id=subject_id, faculty=request.user)
            
            # 1. Authenticate with Gemini
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # 2. DYNAMIC DISCOVERY: Ask Google what models are currently active for this API key
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            if not available_models:
                raise Exception("Your API key does not have access to any text generation models.")
                
            # Prefer a 'flash' model if available, otherwise just grab the first working model on the list
            target_model_name = next((name for name in available_models if 'flash' in name.lower()), available_models[0])
            
            # Load the dynamically found model
            model = genai.GenerativeModel(target_model_name)
            # 3. Prompt Engineering
            prompt = f"""
            You are an expert academic question generator. 
            Generate {num_questions} multiple-choice questions about "{topic}" at a "{difficulty}" difficulty level.
            Return the response STRICTLY as a JSON array of objects. 
            Each object must have exactly these keys:
            - "text": The question statement.
            - "option_a": First option.
            - "option_b": Second option.
            - "option_c": Third option.
            - "option_d": Fourth option.
            - "correct_answer": The correct option letter ("A", "B", "C", or "D").
            """
            
            # 4. Ask the AI!
            response = model.generate_content(prompt)
            # 5. Clean the response and Parse the JSON
            raw_text = response.text
            
            # Gemini sometimes wraps JSON in markdown blocks. This strips them out safely!
            raw_text = raw_text.replace('```json', '').replace('```', '').strip()

            # 5. Parse the JSON and Bulk Save
            questions_data = json.loads(raw_text)
            questions_to_create = []
            
            for q in questions_data:
                questions_to_create.append(Question(
                    subject=subject,
                    text=q['text'],
                    option_a=q['option_a'],
                    option_b=q['option_b'],
                    option_c=q.get('option_c'),
                    option_d=q.get('option_d'),
                    correct_answer=q['correct_answer'],
                    difficulty=difficulty
                ))
                
            Question.objects.bulk_create(questions_to_create)
            
            messages.success(request, f'Magic! Successfully generated and added {len(questions_to_create)} questions about "{topic}".')
            return redirect('question_bank')
            
        except Exception as e:
            messages.error(request, f'AI Generation failed: {str(e)}')
            return redirect('ai_question_generator')

    context = {
        'subjects': subjects,
    }
    return render(request, 'exams/ai_generator.html', context)


