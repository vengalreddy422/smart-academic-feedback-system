from tracemalloc import start

from forms_engine.models import DynamicForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpResponse
from django.db.models import Q

from accounts.models import (
    User,
    StudentProfile,
    TeacherProfile,
    Department,
    Section
)

from django.contrib.auth.decorators import login_required

from django.utils import timezone
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib import messages

from forms_engine.models import (
    PublicFormResponse,
)


from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
import openpyxl
from forms_engine.models import DynamicForm, FormResponse
from reportlab.lib import colors

from collections import Counter
from reportlab.lib.pagesizes import letter

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from collections import Counter
from accounts.models import User

from forms_engine.models import (

    DynamicForm,

    FormQuestion,

    QuestionOption,

    FormResponse,

    PublicFormResponse,

    PublicFormAnswer
)



from reportlab.lib.styles import getSampleStyleSheet

from io import BytesIO

import qrcode
from accounts.models import StudentProfile

from accounts.models import TeacherProfile

from accounts.models import (
    StudentProfile,
)

from forms_engine.models import (
    FormResponse,
    FormAnswer,
)

from functools import wraps
from django.shortcuts import redirect



from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponse

from django.shortcuts import render
from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponse

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('user_login')
            user_role = getattr(request.user, 'role', None)
            if user_role not in roles:
                return HttpResponse('Unauthorized', status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@role_required('teacher')
def teacher_dashboard(request):

    # ==========================================
    # TEACHER PROFILE
    # ==========================================

    teacher_profile = get_object_or_404(
        TeacherProfile.objects.prefetch_related(
            'assigned_sections'
        ),
        user=request.user
    )

    assigned_sections = (
        teacher_profile.assigned_sections.all()
    )

    # ==========================================
    # STUDENTS
    # ==========================================

    students = StudentProfile.objects.filter(
        section__in=assigned_sections
    ).select_related(
        'user',
        'section',
        'department'
    ).distinct()

    total_students = students.count()

    # ==========================================
    # ACTIVE PRIVATE FORMS
    # ==========================================

    today = timezone.now().date()

    forms = DynamicForm.objects.filter(
        access_type='private',
        is_active=True,
        start_date__lte=today,
        deadline_date__gte=today
    ).distinct()

    # ==========================================
    # GET ALL RESPONSES ONCE
    # ==========================================

    all_responses = FormResponse.objects.filter(
        student__section__in=assigned_sections,
        form__in=forms
    ).select_related(
        'student',
        'form'
    )

    # ==========================================
    # GROUP RESPONSES BY FORM
    # ==========================================

    submitted_by_form = {}

    for response in all_responses:

        form_id = response.form_id
        student_id = response.student_id

        if form_id not in submitted_by_form:
            submitted_by_form[form_id] = set()

        submitted_by_form[form_id].add(
            student_id
        )

    # ==========================================
    # ANALYTICS
    # ==========================================

    analytics = []

    for form in forms:

        submitted_ids = submitted_by_form.get(
            form.id,
            set()
        )

        submitted_students = students.filter(
            id__in=submitted_ids
        )

        pending_students = students.exclude(
            id__in=submitted_ids
        )

        analytics.append({

            'form': form,

            'submitted_students':
                submitted_students,

            'pending_students':
                pending_students,

            'submitted_count':
                len(submitted_ids),

            'pending_count':
                total_students - len(submitted_ids),

            'total_students':
                total_students,

            'is_anonymous':
                form.identity_type == 'anonymous',

            'start_date':
                form.start_date,

            'start_time':
                form.start_time,

            'deadline_date':
                form.deadline_date,

            'deadline_time':
                form.deadline_time,
        })

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'teacher_profile':
            teacher_profile,

        'assigned_sections':
            assigned_sections,

        'analytics':
            analytics,

        'total_students':
            total_students,

        'today':
            today,
    }

    return render(
        request,
        'accounts/teacher_dashboard.html',
        context
    )

@role_required('teacher', 'admin')
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

@role_required('teacher')

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

@login_required
def teacher_forms(request):

    if request.user.role != 'teacher':

        return HttpResponse(
            'Unauthorized'
        )

    forms = DynamicForm.objects.all().order_by(
        '-id'
    )

    return render(

        request,

        'accounts/teacher_forms.html',

        {

            'forms': forms,
        }
    )

@role_required('teacher')

def active_forms(request):

    # ==========================================
    # TEACHER PROFILE
    # ==========================================

    teacher_profile = get_object_or_404(

        TeacherProfile.objects.prefetch_related(
            'assigned_sections'
        ),

        user=request.user
    )

    # ==========================================
    # ASSIGNED SECTIONS
    # ==========================================

    assigned_sections = (
        teacher_profile.assigned_sections.all()
    )

    # ==========================================
    # STUDENTS
    # ==========================================

    students = StudentProfile.objects.filter(

        section__in=assigned_sections
    )

    # ==========================================
    # ACTIVE PRIVATE FORMS
    # ==========================================

    forms = DynamicForm.objects.filter(

        access_type='private',

        is_active=True,

        start_date__lte=timezone.now().date(),

        deadline_date__gte=timezone.now().date()

    ).distinct()

    # ==========================================
    # ANALYTICS LIST
    # ==========================================

    analytics = []

    for form in forms:

        # ======================================
        # SUBMITTED STUDENTS
        # ======================================

        submitted_students = students.filter(

            formresponse__form=form

        ).distinct()

        # ======================================
        # PENDING STUDENTS
        # ======================================

        pending_students = students.exclude(

            id__in=submitted_students.values_list(

                'id',

                flat=True
            )
        )

        # ======================================
        # STORE DATA
        # ======================================

        analytics.append({

            'form': form,

            'submitted_count':
                submitted_students.count(),

            'pending_count':
                pending_students.count(),

            'total_students':
                students.count(),
        })

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'analytics': analytics,

        'today': timezone.now().date()
    }

    # ==========================================
    # RENDER
    # ==========================================

    return render(

        request,

        'accounts/active_forms.html',

        context
    )



# ==========================================
# STUDENTS LIST
# ==========================================

@role_required('teacher')
def teacher_completed_forms(request):

    today = timezone.now().date()

    print('TODAY:', today)

    forms = DynamicForm.objects.filter(

        access_type='private',

        is_active=True,

        deadline_date__lt=today
    )

    print('FORMS COUNT:', forms.count())

    for form in forms:

        print(
            form.title,
            form.deadline_date
        )

    context = {

        'forms': forms
    }

    return render(

        request,

        'accounts/teacher_completed_forms.html',

        context
    )

@role_required('teacher')
def teacher_active_forms(request):

    teacher_profile = get_object_or_404(

        TeacherProfile,
        user=request.user
    )

    assigned_sections = (
        teacher_profile.assigned_sections.all()
    )

    today = timezone.now().date()

    forms = DynamicForm.objects.filter(

    access_type='private',

    is_active=True,

    start_date__lte=today,

    deadline_date__gte=today

).distinct()

    analytics = []

    for form in forms:

        total_students = StudentProfile.objects.filter(

            section__in=assigned_sections

        ).count()

        completed_count = FormResponse.objects.filter(

            form=form,

            student__section__in=assigned_sections

        ).count()

        pending_count = (
            total_students - completed_count
        )

        analytics.append({

            'form': form,

            'completed_count': completed_count,

            'pending_count': pending_count,

            'total_students': total_students,
        })

    return render(

        request,

        'accounts/teacher_active_forms.html',

        {

            'analytics': analytics,
        }
    )

@role_required('teacher')
def teacher_upcoming_forms(request):

    teacher_profile = get_object_or_404(

        TeacherProfile,
        user=request.user
    )

    assigned_sections = (
        teacher_profile.assigned_sections.all()
    )

    today = timezone.now().date()

    forms = DynamicForm.objects.filter(

    access_type='private',

    is_active=True,

    start_date__gt=today
).distinct()

    analytics = []

    for form in forms:

        total_students = StudentProfile.objects.filter(

            section__in=assigned_sections

        ).count()

        analytics.append({

            'form': form,

            'total_students': total_students,
        })

    return render(

        request,

        'accounts/teacher_upcoming_forms.html',

        {

            'analytics': analytics,
        }
    )

@role_required('teacher')
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
