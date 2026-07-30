from tracemalloc import start
from forms_engine.models import DynamicForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from accounts.models import User, StudentProfile, TeacherProfile, Department, Section
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from forms_engine.models import DynamicForm, FormQuestion, QuestionOption, FormResponse, PublicFormResponse, PublicFormAnswer, FormAnswer
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_protect
from collections import Counter
from io import BytesIO
import qrcode
from django.core.files import File
from functools import wraps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import update_session_auth_hash


def teacher_form_detail(request, form_id):

    # ==========================================
    # GET FORM
    # ==========================================

    form = get_object_or_404(
        DynamicForm,
        id=form_id
    )

    # ==========================================
    # ADMIN / TEACHER STUDENTS
    # ==========================================

    if request.user.role == 'admin':

        students = (
            StudentProfile.objects
            .select_related(
                'user',
                'section',
                'department'
            )
            .all()
        )

        assigned_sections = None

    else:

        teacher_profile = get_object_or_404(
            TeacherProfile.objects.prefetch_related(
                'assigned_sections'
            ),
            user=request.user
        )

        assigned_sections = (
            teacher_profile.assigned_sections.all()
        )

        students = (
            StudentProfile.objects.filter(
                section__in=assigned_sections
            )
            .select_related(
                'user',
                'section',
                'department'
            )
        )

    # ==========================================
    # SUBMITTED STUDENTS
    # ==========================================

    submitted_students = students.filter(
        formresponse__form=form
    ).distinct()

    submitted_ids = list(
        submitted_students.values_list(
            'id',
            flat=True
        )
    )

    # ==========================================
    # PENDING STUDENTS
    # ==========================================

    pending_students = students.exclude(
        id__in=submitted_ids
    )

    # ==========================================
    # QUESTIONS
    # ==========================================

    questions = FormQuestion.objects.filter(
        form=form
    ).order_by(
        '-is_system_field',
        'order',
        'id'
    )

    # ==========================================
    # LOAD ALL ANSWERS ONCE
    # ==========================================

    if request.user.role == 'admin':

        all_answers = (
            FormAnswer.objects.filter(
                response__form=form
            )
            .select_related(
                'question',
                'response'
            )
        )

    else:

        all_answers = (
            FormAnswer.objects.filter(
                response__form=form,
                response__student__section__in=assigned_sections
            )
            .select_related(
                'question',
                'response'
            )
        )

    # ==========================================
    # GROUP ANSWERS BY QUESTION
    # ==========================================

    answers_by_question = {}

    for answer in all_answers:

        question_id = answer.question_id

        if question_id not in answers_by_question:
            answers_by_question[
                question_id
            ] = []

        if answer.answer:
            answers_by_question[
                question_id
            ].append(
                answer.answer
            )

    # ==========================================
    # ANALYTICS
    # ==========================================

    question_analytics = []

    text_questions = []

    for question in questions:

        answer_list = (
            answers_by_question.get(
                question.id,
                []
            )
        )

        field_type = str(
            question.field_type
        ).lower().strip()

        # ======================================
        # RADIO
        # ======================================

        if 'radio' in field_type:

            answer_counts = Counter(
                answer_list
            )

            question_analytics.append({

                'question':
                    question.question,

                'labels':
                    list(answer_counts.keys()),

                'values':
                    list(answer_counts.values()),

                'chart_type':
                    'pie',

                'field_type':
                    field_type
            })

        # ======================================
        # DROPDOWN / SELECT
        # ======================================

        elif (
            'dropdown' in field_type
            or
            'select' in field_type
        ):

            answer_counts = Counter(
                answer_list
            )

            question_analytics.append({

                'question':
                    question.question,

                'labels':
                    list(answer_counts.keys()),

                'values':
                    list(answer_counts.values()),

                'chart_type':
                    'bar',

                'field_type':
                    field_type
            })

        # ======================================
        # RATING
        # ======================================

        elif 'rating' in field_type:

            answer_counts = Counter(
                answer_list
            )

            question_analytics.append({

                'question':
                    question.question,

                'labels':
                    list(answer_counts.keys()),

                'values':
                    list(answer_counts.values()),

                'chart_type':
                    'bar'
            })

        # ======================================
        # CHECKBOX
        # ======================================

        elif 'checkbox' in field_type:

            checkbox_answers = []

            for value in answer_list:

                split_values = value.split(',')

                for item in split_values:

                    cleaned = item.strip()

                    if cleaned:

                        checkbox_answers.append(
                            cleaned
                        )

            answer_counts = Counter(
                checkbox_answers
            )

            question_analytics.append({

                'question':
                    question.question,

                'labels':
                    list(answer_counts.keys()),

                'values':
                    list(answer_counts.values()),

                'chart_type':
                    'bar'
            })

        # ======================================
        # TEXTAREA
        # ======================================

        elif 'textarea' in field_type:

            question_analytics.append({

                'question':
                    question.question,

                'answers':
                    answer_list,

                'chart_type':
                    'text'
            })

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'form': form,

        'students': students,

        'submitted_students':
            submitted_students,

        'pending_students':
            pending_students,

        'question_analytics':
            question_analytics,

        'text_questions':
            text_questions,
    }

    return render(
        request,
        'accounts/teacher_form_detail.html',
        context
    )

def student_response_detail(request, response_id):

    response = FormResponse.objects.select_related(
        'student',
        'student__user',
        'form',
    ).get(
        id=response_id
    )

    answers = FormAnswer.objects.filter(
        response=response
    ).select_related(
        'question'
    )

    context = {

        'response': response,

        'answers': answers,
    }

    return render(

        request,

        'accounts/student_response_detail.html',

        context
    )

def teacher_students(request):

    teacher_profile = get_object_or_404(

        TeacherProfile.objects.prefetch_related(
            'assigned_sections'
        ),

        user=request.user
    )

    assigned_sections = (
        teacher_profile.assigned_sections.all()
    )

    students = StudentProfile.objects.filter(

    section__in=assigned_sections

    ).select_related(

        'user',
        'section',
        'department'

    ).distinct()

    # ==========================================
    # SEARCH
    # ==========================================

    search = request.GET.get('search')

    if search:

        students = students.filter(

            Q(user__first_name__icontains=search)

            |

            Q(user__last_name__icontains=search)

            |

            Q(roll_number__icontains=search)
        )
    context = {

        'students': students,
    }

    return render(

        request,

        'accounts/teacher_students.html',

        context
    )