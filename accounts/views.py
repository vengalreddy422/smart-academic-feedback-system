from forms_engine.models import DynamicForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpResponse
from django.db.models import Q

from .models import (
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
from .models import User

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
from .models import StudentProfile

from .models import TeacherProfile

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


def information_page(request):
    
    return render(

        request,

        'accounts/information_page.html'
    )

def role_required(*roles):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(

            request,

            *args,

            **kwargs
        ):

            # ==========================
            # NOT LOGGED IN
            # ==========================

            if not request.user.is_authenticated:

                return redirect(

                    'login'
                )

            # ==========================
            # SAFE ROLE CHECK
            # ==========================

            user_role = getattr(

                request.user,

                'role',

                None
            )

            # ==========================
            # UNAUTHORIZED ROLE
            # ==========================

            if user_role not in roles:

                return HttpResponse(

                    'Unauthorized',

                    status=403
                )

            # ==========================
            # ACCESS ALLOWED
            # ==========================

            return view_func(

                request,

                *args,

                **kwargs
            )

        return wrapper

    return decorator

@csrf_protect
def user_login(request):

    # ==========================
    # ALREADY LOGGED IN
    # ==========================

    if request.user.is_authenticated:

        if request.user.role == 'admin':

            return redirect(
                reverse('admin_dashboard')
            )

        if request.user.role == 'teacher':

            return redirect(
                reverse('teacher_dashboard')
            )

        if request.user.role == 'student':

            return redirect(
                reverse('student_dashboard')
            )

    # ==========================
    # LOGIN POST
    # ==========================

    if request.method == 'POST':

        username = request.POST.get(
            'username'
        )

        password = request.POST.get(
            'password'
        )

        user = authenticate(

            request,

            username=username,

            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            # ==========================
            # SESSION PERSISTENCE
            # ==========================

            request.session.set_expiry(
                86400
            )

            if user.role == 'admin':

                return redirect(
                    reverse('admin_dashboard')
                )

            if user.role == 'teacher':

                return redirect(
                    reverse('teacher_dashboard')
                )

            if user.role == 'student':

                return redirect(
                    reverse('student_dashboard')
                )

            return HttpResponse(

                'Role Not Found',

                status=403
            )

        return render(

            request,

            'accounts/login.html',

            {

                'error':
                'Invalid Username or Password'

            },

        )

    return render(

        request,

        'accounts/login.html'
    )
@login_required
@role_required('admin')
def admin_dashboard(request):

    # ==========================================
    # TODAY
    # ==========================================

    today = timezone.now().date()

    # ==========================================
    # TOTAL COUNTS
    # ==========================================

    total_students = StudentProfile.objects.count()

    total_teachers = TeacherProfile.objects.count()

    total_forms = DynamicForm.objects.count()

    # ==========================================
    # TOTAL RESPONSES
    # ==========================================

    total_private_responses = FormResponse.objects.count()

    total_public_responses = PublicFormResponse.objects.count()

    total_responses = (

        total_private_responses
        +
        total_public_responses
    )

    # ==========================================
    # RECENT FORMS
    # ==========================================

    recent_forms = DynamicForm.objects.order_by(

        '-created_at'

    )[:5]

    # ==========================================
    # RECENT STUDENTS
    # ==========================================

    recent_students = StudentProfile.objects.select_related(

        'user'

    ).order_by(

        '-id'

    )[:5]

    # ==========================================
    # RECENT TEACHERS
    # ==========================================

    recent_teachers = TeacherProfile.objects.select_related(

        'user'

    ).order_by(

        '-id'

    )[:5]

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'today': today,

        'total_students': total_students,

        'total_teachers': total_teachers,

        'total_forms': total_forms,

        'total_responses': total_responses,

        'recent_forms': recent_forms,

        'recent_students': recent_students,

        'recent_teachers': recent_teachers,
    }

    return render(

        request,

        'accounts/admin_dashboard.html',

        context
    )
    
@login_required
@role_required('teacher')
def teacher_dashboard(request):

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
    )

    # ==========================================
    # ONLY PRIVATE FORMS
    # ==========================================

    # ==========================================
# ACTIVE FORMS ONLY
# ==========================================

    today = timezone.now().date()

    forms = DynamicForm.objects.filter(

        access_type='private',

        is_active=True,

        start_date__lte=today,

        deadline_date__gte=today

    ).distinct()

    analytics = []

    for form in forms:

        submitted_students = students.filter(

            formresponse__form=form

        ).distinct()

        pending_students = students.exclude(

            id__in=submitted_students.values_list(

                'id',

                flat=True
            )
        )

        analytics.append({

    'form': form,

    'submitted_students': submitted_students,

    'pending_students': pending_students,

    'submitted_count': submitted_students.count(),

    'pending_count': pending_students.count(),

    'total_students': students.count(),

    # ==================================
    # ANONYMOUS CHECK
    # ==================================

    'is_anonymous':

        form.identity_type == 'anonymous',

    # ==================================
    # START DATE
    # ==================================

    'start_date': form.start_date,

    'start_time': form.start_time,

    # ==================================
    # DEADLINE
    # ==================================

    'deadline_date': form.deadline_date,

    'deadline_time': form.deadline_time,})

    total_students = StudentProfile.objects.filter(

    section__in=assigned_sections

    ).distinct().count()

    context = {

    'teacher_profile': teacher_profile,

    'assigned_sections': assigned_sections,

    'analytics': analytics,

    'total_students': total_students,

    'today': timezone.now().date(),}

    return render(

        request,

        'accounts/teacher_dashboard.html',

        context
    )
    
@login_required
@role_required('student')
def student_dashboard(request):

    # ==========================================
    # STUDENT PROFILE
    # ==========================================

    student_profile = get_object_or_404(

        StudentProfile,

        user=request.user
    )

    # ==========================================
    # TODAY DATE
    # ==========================================

    today = timezone.now().date()

    # ==========================================
    # ONLY PRIVATE ACTIVE FORMS
    # ==========================================

    all_forms = DynamicForm.objects.filter(

        access_type='private',

        is_active=True

    ).distinct()

    # ==========================================
    # SUBMITTED FORM IDS
    # ==========================================

    submitted_form_ids = FormResponse.objects.filter(

        student=student_profile

    ).values_list(

        'form_id',

        flat=True
    )

    # ==========================================
    # PENDING / ACTIVE FORMS
    # ==========================================

    pending_forms = all_forms.filter(

        start_date__lte=today,

        deadline_date__gte=today

    ).exclude(

        id__in=submitted_form_ids
    )

    # ==========================================
    # UPCOMING FORMS
    # ==========================================

    upcoming_forms = all_forms.filter(

        start_date__gt=today

    ).exclude(

        id__in=submitted_form_ids
    )

    # ==========================================
    # COMPLETED FORMS
    # ==========================================

    completed_forms = all_forms.filter(

    id__in=submitted_form_ids,

    
)

    # ==========================================
    # EXPIRED FORMS
    # ==========================================

    expired_forms = all_forms.filter(

        deadline_date__lt=today

    ).exclude(

        id__in=submitted_form_ids
    )

    # ==========================================
    # COUNTS
    # ==========================================

    total_forms_count = all_forms.count()

    pending_forms_count = pending_forms.count()

    upcoming_forms_count = upcoming_forms.count()

    completed_forms_count = completed_forms.count()

    expired_forms_count = expired_forms.count()

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'student_profile': student_profile,

        # ======================================
        # FORM LISTS
        # ======================================

        'pending_forms': pending_forms,

        'upcoming_forms': upcoming_forms,

        'completed_forms': completed_forms,

        'expired_forms': expired_forms,

        # ======================================
        # COUNTS
        # ======================================

        'total_forms_count': total_forms_count,

        'pending_forms_count': pending_forms_count,

        'upcoming_forms_count': upcoming_forms_count,

        'completed_forms_count': completed_forms_count,

        'expired_forms_count': expired_forms_count,
    }

    # ==========================================
    # RENDER TEMPLATE
    # ==========================================

    return render(

        request,

        'accounts/student_dashboard.html',

        context
    )

def user_logout(request):

    logout(request)

    return redirect(
        reverse('login')
    )


from django.contrib.auth.views import PasswordChangeView

from django.contrib.auth import update_session_auth_hash

from django.urls import reverse_lazy


from django.contrib.auth.views import PasswordChangeView

from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth import update_session_auth_hash

from django.urls import reverse_lazy


class UserPasswordChangeView(

    LoginRequiredMixin,

    PasswordChangeView

):

    template_name = 'accounts/password_change.html'

    success_url = reverse_lazy('student_dashboard')

    def form_valid(self, form):

        response = super().form_valid(form)

        # KEEP USER LOGGED IN

        update_session_auth_hash(

            self.request,

            form.user

        )

        return response
    
@login_required
@role_required('teacher', 'admin')

def teacher_form_detail(request, form_id):

    form = get_object_or_404(
        DynamicForm,
        id=form_id
    )

    # ==========================================
    # ADMIN ACCESS
    # ==========================================

    if request.user.role == 'admin':

        students = StudentProfile.objects.all()

    else:

        teacher_profile = get_object_or_404(
            TeacherProfile.objects.prefetch_related(
                'assigned_sections'
            ),
            user=request.user
        )

        assigned_sections = teacher_profile.assigned_sections.all()

        students = StudentProfile.objects.filter(
            section__in=assigned_sections
        )

    # ==========================================
    # SUBMITTED STUDENTS
    # ==========================================

    submitted_students = students.filter(
        formresponse__form=form
    ).distinct()

    # ==========================================
    # PENDING STUDENTS
    # ==========================================

    pending_students = students.exclude(
        id__in=submitted_students.values_list(
            'id',
            flat=True
        )
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
    # ANALYTICS
    # ==========================================

    question_analytics = []

    text_questions = []

    for question in questions:

        answers = FormAnswer.objects.filter(
            question=question
        )

        answer_list = []

        for answer in answers:

            if answer.answer:

                answer_list.append(
                    answer.answer
                )

        field_type = str(
            question.field_type
        ).lower().strip()

        # ==========================================
        # RADIO
        # ==========================================

        if 'radio' in field_type:

            answer_counts = Counter(
                answer_list
            )

            question_analytics.append({

                'question': question.question,

                'labels': list(answer_counts.keys()),

                'values': list(answer_counts.values()),

                'chart_type': 'pie',
                'field_type': field_type
            })

        # ==========================================
        # DROPDOWN
        # ==========================================

        elif (

            'dropdown' in field_type

            or

            'select' in field_type
        ):

            answer_counts = Counter(
                answer_list
            )

            question_analytics.append({

                'question': question.question,

                'labels': list(answer_counts.keys()),

                'values': list(answer_counts.values()),

                'chart_type': 'bar',
                'field_type': field_type
            })
            
        # ==========================================
        # RATING FIELD
        # ==========================================

        elif 'rating' in field_type:

            answer_counts = Counter(
                answer_list
            )

            question_analytics.append({

                'question': question.question,

                'labels': list(answer_counts.keys()),

                'values': list(answer_counts.values()),

                'chart_type': 'bar'
            })
        # ==========================================
        # CHECKBOX
        # ==========================================

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

                'question': question.question,

                'labels': list(answer_counts.keys()),

                'values': list(answer_counts.values()),

                'chart_type': 'bar'
            })

        # ==========================================
        # TEXT FIELDS
        # ==========================================

        elif 'textarea' in field_type:
    
            question_analytics.append({

                'question': question.question,

                'answers': answer_list,

                'chart_type': 'text'
            })

    context = {

        'form': form,

        'students': students,

        'submitted_students': submitted_students,

        'pending_students': pending_students,

        'question_analytics': question_analytics,

        'text_questions': text_questions,
    }

    return render(

        request,

        'accounts/teacher_form_detail.html',

        context
    )

@login_required    
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
def manage_users(request):

    if request.user.role != 'admin':

        return HttpResponse(
            'Unauthorized'
        )

    if request.method == 'POST':

        full_name = request.POST.get(
            'full_name'
        )

        username = request.POST.get(
            'username'
        )

        password = request.POST.get(
            'password'
        )

        role = request.POST.get(
            'role'
        )

        user = User.objects.create_user(

            username=username,

            password=password,

            role=role,
        )

        user.first_name = full_name

        user.save()

    users = User.objects.all().order_by(
        '-id'
    )

    return render(

        request,

        'accounts/manage_users.html',

        {

            'users': users,
        }
    )

@login_required
def teachers_list(request):

    if request.user.role != 'admin':

        return HttpResponse(
            'Unauthorized'
        )

    # ==========================================
    # TEACHERS
    # ==========================================

    teachers = TeacherProfile.objects.select_related(
        'user',
        'department'
    )

    # ==========================================
    # SEARCH
    # ==========================================

    search = request.GET.get(
        'search'
    )

    if search:

        teachers = teachers.filter(

            Q(user__first_name__icontains=search) |

            Q(user__username__icontains=search)
        )

    teachers = teachers.order_by(
        '-id'
    )

    return render(

        request,

        'accounts/teachers_list.html',

        {

            'teachers': teachers,
        }
    )
    
@login_required
def private_forms(request):

    if request.user.role != 'admin':

        return HttpResponse(
            'Unauthorized'
        )

    # ==========================================
    # TODAY
    # ==========================================

    today = timezone.now().date()

    # ==========================================
    # GET PRIVATE FORMS
    # ==========================================

    forms = DynamicForm.objects.filter(
        access_type='private'
    )

    analytics = []

    for form in forms:

        total_students = StudentProfile.objects.count()

        submitted_students = StudentProfile.objects.filter(

            formresponse__form=form

        ).distinct()

        submitted_count = submitted_students.count()

        pending_count = (

            total_students
            -
            submitted_count
        )

        # ==========================================
        # ANONYMOUS FORM
        # ==========================================

        if form.identity_type == 'anonymous':

            analytics.append({

                'form': form,

                'total_students': total_students,

                'submitted_count': submitted_count,

                'pending_count': pending_count,

                'students': [],

                'is_anonymous': True
            })

        # ==========================================
        # IDENTIFIED FORM
        # ==========================================

        else:

            analytics.append({

                'form': form,

                'total_students': total_students,

                'submitted_count': submitted_count,

                'pending_count': pending_count,

                'students': submitted_students,

                'is_anonymous': False
            })

    context = {

        'analytics': analytics,

        'today': today
    }

    return render(

        request,

        'accounts/private_forms.html',

        context
    )
    
@login_required
def public_forms(request):

    forms = DynamicForm.objects.filter(
        access_type='public'
    )

    analytics = []

    for form in forms:

        total_responses = PublicFormResponse.objects.filter(
            form=form
        ).count()

        analytics.append({

            'form': form,

            'total_responses': total_responses,
        })

    return render(

        request,

        'accounts/public_forms.html',

        {

            'analytics': analytics,
        }
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

@login_required
def public_form_qr(request, form_id):

    if request.user.role != 'admin':

        return HttpResponse(
            'Unauthorized'
        )

    form = get_object_or_404(

        DynamicForm,

        id=form_id
    )

    ip_address = '192.168.1.95'

    public_url = (

        f'http://{ip_address}:8000'

        f'/forms/public-form/{form.uuid}/'
    )

    qr = qrcode.make(

        public_url
    )

    buffer = BytesIO()

    qr.save(

        buffer,

        format='PNG'
    )

    return HttpResponse(

        buffer.getvalue(),

        content_type='image/png'
    )
@login_required
def public_form_users(request, form_id):

    if request.user.role != 'admin':

        return HttpResponse(
            'Unauthorized'
        )

    # ==========================================
    # GET FORM
    # ==========================================

    form = get_object_or_404(

        DynamicForm,

        id=form_id
    )

    # ==========================================
    # ANONYMOUS FORM
    # ==========================================

    if form.identity_type == 'anonymous':

        total_responses = PublicFormResponse.objects.filter(

            form=form
        ).count()

        context = {

            'form': form,

            'is_anonymous': True,

            'total_responses': total_responses,
        }

        return render(

            request,

            'accounts/public_form_users.html',

            context
        )

    # ==========================================
    # IDENTIFIED FORM
    # ==========================================

    allowed_keywords = [

        'name',

        'email',

        'college',

        'department',

        'course',

        'roll',

        'phone',

        'mobile'
    ]

    all_questions = FormQuestion.objects.filter(

        form=form

    ).order_by(

        '-is_system_field',

        'order',

        'id'

    )



    filtered_questions = []

    for question in all_questions:

        question_text = question.question.lower()

        for keyword in allowed_keywords:

            if keyword in question_text:

                filtered_questions.append(question)

                break

    responses = PublicFormResponse.objects.filter(

        form=form

    ).prefetch_related(

        'publicformanswer_set'
    )

    context = {

        'form': form,

        'questions': filtered_questions,

        'responses': responses,

        'is_anonymous': False
    }

    return render(

        request,

        'accounts/public_form_users.html',

        context
    )
    
from collections import Counter
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
# Make sure to import your models here (DynamicForm, PublicFormResponse, FormQuestion, PublicFormAnswer)

@login_required
def public_form_detail(request, form_id):

    # ==========================================
    # ADMIN CHECK
    # ==========================================
    if request.user.role != 'admin':
        return HttpResponse('Unauthorized')

    # ==========================================
    # GET FORM
    # ==========================================
    form = get_object_or_404(DynamicForm, id=form_id)

    # ==========================================
    # RESPONSES
    # ==========================================
    responses = PublicFormResponse.objects.filter(form=form)
    total_responses = responses.count()

    # ==========================================
    # QUESTIONS
    # ==========================================
    questions = FormQuestion.objects.filter(form=form).order_by(
        '-is_system_field',
        'order',
        'id'
    )   

    # ==========================================
    # ANALYTICS & TEXT CONTAINERS
    # ==========================================
    question_analytics = []
    text_questions = []

    # ==========================================
    # LOOP QUESTIONS
    # ==========================================
    for question in questions:

        # ======================================
        # SKIP SYSTEM FIELDS
        # ======================================
        if question.is_system_field:
            continue

        # ======================================
        # GET ANSWERS
        # ======================================
        answers = PublicFormAnswer.objects.filter(question=question)

        # ======================================
        # TEXT RESPONSES (TEXTAREA ONLY)
        # ======================================
        if question.field_type == 'textarea':
            text_answer_list = []
            for answer in answers:
                if answer.answer.strip():
                    text_answer_list.append(answer.answer)

            text_questions.append({
                'question': question.question,
                'answers': text_answer_list,
            })

        # ======================================
        # VISUALIZATION QUESTIONS (RATING, CHECKBOX, SELECT, RADIO)
        # ======================================
        elif question.field_type in ['radio', 'checkbox', 'select', 'rating']:
            answer_list = []
            for answer in answers:
                
                # Checkbox items handling
                if ',' in answer.answer:
                    split_answers = answer.answer.split(',')
                    for item in split_answers:
                        clean_item = item.strip()
                        if clean_item:
                            answer_list.append(clean_item)
                else:
                    if answer.answer.strip():
                        answer_list.append(answer.answer)

            # ==================================
            # COUNTS & LABELS
            # ==================================
            answer_counts = Counter(answer_list)
            labels = list(answer_counts.keys())
            values = list(answer_counts.values())

            # ==================================
            # EMPTY CHECK & CHART TYPE ASSIGNMENT
            # ==================================
            if labels and values:
                if question.field_type == 'checkbox':
                    chart_type = 'bar'
                else:
                    chart_type = 'pie'

                question_analytics.append({
                    'question': question.question,
                    'labels': labels,
                    'values': values,
                    'chart_type': chart_type,
                })

    # ==========================================
    # CONTEXT
    # ==========================================
    context = {
        'form': form,
        'responses': responses,
        'total_responses': total_responses,
        'question_analytics': question_analytics,
        'text_questions': text_questions,
    }

    # ==========================================
    # RENDER
    # ==========================================
    return render(request, 'accounts/public_form_detail.html', context)


@login_required
@role_required('admin')
def edit_form(request, form_id):

    form = get_object_or_404(

        DynamicForm,

        id=form_id
    )

    questions = FormQuestion.objects.filter(

    form=form

    ).order_by(

        'order'
    )

    if request.method == 'POST':

        # ==========================================
        # FORM UPDATE
        # ==========================================

        form.title = request.POST.get(

            'title'
        )

        form.description = request.POST.get(

            'description'
        )

        form.start_date = request.POST.get(

            'start_date'
        )

        form.deadline_date = request.POST.get(

            'deadline_date'
        )

        form.is_active = (

            request.POST.get(

                'is_active'
            ) == 'on'
        )

        form.save()

        # ==========================================
        # QUESTIONS
        # ==========================================

        for question in questions:

            question.question = request.POST.get(

                f'question_{question.id}'
            )

            question.required = (

                request.POST.get(

                    f'required_{question.id}'
                ) == 'on'
            )

            question.save()

            # ==========================================
            # OPTIONS
            # ==========================================

            for option in question.question_options.all():
    
                option_value = request.POST.get(

                    f'option_{option.id}'
                )

                # ======================================
                # PREVENT NULL VALUES
                # ======================================

                if option_value:

                    option.option_text = option_value

                    option.save()

                    return redirect(

                        'private_forms'
                    )

    return render(

        request,

        'accounts/edit_form.html',

        {

            'form': form,

            'questions': questions,
        }
    )
@login_required
@role_required('admin')

def delete_form(request, form_id):

    form = get_object_or_404(

        DynamicForm,

        id=form_id
    )

    if request.method == 'POST':

        form.delete()

        return redirect(

            'private_forms'
        )

    return render(

        request,

        'accounts/delete_form.html',

        {

            'form': form
        }
    )
@login_required
@role_required('admin')

def add_question(request, form_id):

    form = get_object_or_404(

        DynamicForm,

        id=form_id
    )

    # ==========================================
    # POST REQUEST
    # ==========================================

    if request.method == 'POST':

        field_type = request.POST.get(

            'field_type'
        )

        # ==========================================
        # CREATE QUESTION
        # ==========================================

        question = FormQuestion.objects.create(

            form=form,

            question=request.POST.get(

                'question'
            ),

            field_type=field_type,

            required=(

                request.POST.get(

                    'required'
                ) == 'on'
            ),

            order=FormQuestion.objects.filter(

                form=form

            ).count() + 1
        )

        # ==========================================
        # OPTIONS
        # ==========================================

        if field_type in [

            'radio',
            'checkbox',
            'select'
        ]:

            # GET MULTIPLE OPTION INPUTS

            options_list = request.POST.getlist(

                'options'
            )

            for option in options_list:

                if option.strip():

                    QuestionOption.objects.create(

                        question=question,

                        option_text=option.strip()
                    )

        # ==========================================
        # REDIRECT
        # ==========================================

        return redirect(

            'edit_form',

            form_id=form.id
        )

    # ==========================================
    # GET REQUEST
    # ==========================================

    return render(

        request,

        'accounts/add_question.html',

        {

            'form': form
        }
    )
@login_required
@role_required('admin')

def delete_question(request, question_id):

    question = get_object_or_404(

        FormQuestion,

        id=question_id
    )

    form_id = question.form.id

    question.delete()

    return redirect(

        'edit_form',

        form_id=form_id
    )

@login_required
@role_required('admin')

def delete_option(request, option_id):

    option = get_object_or_404(

        QuestionOption,

        id=option_id
    )

    form_id = option.question.form.id

    option.delete()

    return redirect(

        'edit_form',

        form_id=form_id
    )
@login_required
@role_required('admin')

def preview_form(request, form_id):

    form = get_object_or_404(

        DynamicForm,

        id=form_id
    )

    questions = FormQuestion.objects.filter(

        form=form

    ).order_by(

        'order'
    )

    return render(

        request,

        'accounts/preview_form.html',

        {

            'form': form,

            'questions': questions,
        }
    )


@login_required
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

@login_required
def students_list(request):

    if request.user.role != 'admin':

        return HttpResponse(
            'Unauthorized'
        )

    # ==========================================
    # SEARCH
    # ==========================================

    search = request.GET.get(
        'search'
    )

    students = StudentProfile.objects.select_related(

        'user',
        'department',
        'section'
    )

    # ==========================================
    # SEARCH FILTER
    # ==========================================

    if search:

        students = students.filter(

            Q(user__first_name__icontains=search)

            |

            Q(user__last_name__icontains=search)

            |

            Q(user__username__icontains=search)

            |

            Q(roll_number__icontains=search)

            |

            Q(department__name__icontains=search)

            |

            Q(section__name__icontains=search)
        )

    # ==========================================
    # ORDERING
    # ==========================================

    students = students.order_by(

        'department__name',

        'section__name'
    )

    # ==========================================
    # GROUPED DATA
    # ==========================================

    grouped_data = {}

    for student in students:

        department_name = (
            student.department.name
        )

        section_name = (
            student.section.name
        )

        # CREATE DEPARTMENT

        if department_name not in grouped_data:

            grouped_data[
                department_name
            ] = {}

        # CREATE SECTION

        if section_name not in grouped_data[
            department_name
        ]:

            grouped_data[
                department_name
            ][section_name] = []

        # APPEND STUDENT

        grouped_data[
            department_name
        ][section_name].append(student)

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'grouped_data': grouped_data
    }

    return render(

        request,

        'accounts/students_list.html',

        context
    )
    
@login_required
@role_required('student')
def completed_forms(request):

    student_profile = get_object_or_404(

        StudentProfile,

        user=request.user
    )

    submitted_form_ids = FormResponse.objects.filter(

        student=student_profile

    ).values_list(

        'form_id',

        flat=True
    )

    forms = DynamicForm.objects.filter(

        id__in=submitted_form_ids
    )

    context = {

        'forms': forms,
    }

    return render(

        request,

        'accounts/completed_forms.html',

        context
    )


@login_required
@role_required('student')
def upcoming_forms(request):

    # ==========================================
    # STUDENT PROFILE
    # ==========================================

    student_profile = get_object_or_404(

        StudentProfile,

        user=request.user
    )

    # ==========================================
    # TODAY
    # ==========================================

    today = timezone.now().date()

    # ==========================================
    # SUBMITTED FORMS
    # ==========================================

    submitted_form_ids = FormResponse.objects.filter(

        student=student_profile

    ).values_list(

        'form_id',

        flat=True
    )

    # ==========================================
    # UPCOMING PRIVATE FORMS ONLY
    # ==========================================

    forms = DynamicForm.objects.filter(

        access_type='private',

        is_active=True,

        start_date__gt=today

    ).exclude(

        id__in=submitted_form_ids
    )

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'forms': forms
    }

    # ==========================================
    # RENDER
    # ==========================================

    return render(

        request,

        'accounts/upcoming_forms.html',

        context
    )
    
@login_required
@role_required('student')
def pending_forms(request):

    student_profile = get_object_or_404(

        StudentProfile,

        user=request.user
    )

    today = timezone.now().date()

    all_forms = DynamicForm.objects.filter(

        access_type='private',

        is_active=True
    ).distinct()

    submitted_form_ids = FormResponse.objects.filter(

        student=student_profile

    ).values_list(

        'form_id',

        flat=True
    )

    forms = all_forms.filter(

        start_date__lte=today,

        deadline_date__gte=today

    ).exclude(

        id__in=submitted_form_ids
    )

    context = {

        'forms': forms,

        'today': today,
    }

    return render(

        request,

        'accounts/pending_forms.html',

        context
    )
    
@login_required
@role_required('student')
def expired_forms(request):

    student_profile = get_object_or_404(

        StudentProfile,


        user=request.user
    )

    today = timezone.now().date()

    submitted_form_ids = FormResponse.objects.filter(

        student=student_profile

    ).values_list(

        'form_id',

        flat=True
    )

    forms = DynamicForm.objects.filter(

        access_type='private',

        is_active=True,

        deadline_date__lt=today

    ).exclude(

        id__in=submitted_form_ids
    )

    context = {

        'forms': forms
    }

    return render(

        request,

        'accounts/expired_forms.html',

        context
    )
    
@login_required
@login_required
def add_student(request):

    departments = Department.objects.all()

    sections = Section.objects.all()

    # ==========================================
    # CREATE STUDENT
    # ==========================================

    if request.method == 'POST':

        username = request.POST.get(

            'username'
        )

        roll_number = request.POST.get(

            'roll_number'
        )

        # ==========================================
        # CHECK DUPLICATE USERNAME
        # ==========================================

        if User.objects.filter(

            username=username

        ).exists():

            messages.error(

                request,

                'Username already exists.'
            )

            context = {

                'departments': departments,

                'sections': sections
            }

            return render(

                request,

                'accounts/add_student.html',

                context
            )

        # ==========================================
        # CHECK DUPLICATE ROLL NUMBER
        # ==========================================

        if StudentProfile.objects.filter(

            roll_number=roll_number

        ).exists():

            messages.error(

                request,

                'Roll number already exists.'
            )

            context = {

                'departments': departments,

                'sections': sections
            }

            return render(

                request,

                'accounts/add_student.html',

                context
            )

        # ==========================================
        # CREATE USER
        # ==========================================

        user = User.objects.create_user(

            username=username,

            password=request.POST.get(
                'password'
            ),

            first_name=request.POST.get(
                'first_name'
            ),

            last_name=request.POST.get(
                'last_name'
            ),

            email=request.POST.get(
                'email'
            ),

            role='student'
        )

        # ==========================================
        # CREATE PROFILE
        # ==========================================

        StudentProfile.objects.create(

            user=user,

            department_id=request.POST.get(
                'department'
            ),

            section_id=request.POST.get(
                'section'
            ),

            roll_number=roll_number,

            semester=request.POST.get(
                'semester'
            ),

            phone_number=request.POST.get(
                'phone_number'
            )
        )

        # ==========================================
        # SUCCESS MESSAGE
        # ==========================================

        messages.success(

            request,

            'Student added successfully.'
        )

        return redirect(

            'students_list'
        )

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'departments': departments,

        'sections': sections
    }

    return render(

        request,

        'accounts/add_student.html',

        context
    )
    
@login_required
def edit_student(request, student_id):

    student = get_object_or_404(

        StudentProfile.objects.select_related(
            'user'
        ),

        id=student_id
    )

    departments = Department.objects.all()

    sections = Section.objects.all()

    # ==========================================
    # UPDATE
    # ==========================================

    if request.method == 'POST':

        # USER

        student.user.first_name = request.POST.get(
            'first_name'
        )

        student.user.last_name = request.POST.get(
            'last_name'
        )

        student.user.email = request.POST.get(
            'email'
        )

        student.user.save()

        # PROFILE

        student.roll_number = request.POST.get(
            'roll_number'
        )

        student.semester = request.POST.get(
            'semester'
        )

        student.phone_number = request.POST.get(
            'phone_number'
        )

        student.department_id = request.POST.get(
            'department'
        )

        student.section_id = request.POST.get(
            'section'
        )

        student.save()

        if request.user.role == 'teacher':
            
            return redirect(
                'teacher_students'
            )

        return redirect(
            'students_list'
        )

    context = {

        'student': student,

        'departments': departments,

        'sections': sections
    }

    return render(

        request,

        'accounts/edit_student.html',

        context
    )
    
    
@login_required
def delete_student(request, student_id):

    student = get_object_or_404(

        StudentProfile.objects.select_related(
            'user'
        ),

        id=student_id
    )

    # ==========================================
    # DELETE
    # ==========================================

    if request.method == 'POST':

        student.user.delete()

        if request.user.role == 'teacher':
    
            return redirect(
                'teacher_students'
            )

        return redirect(
            'students_list'
        )

    return render(

        request,

        'accounts/delete_student.html',

        {

            'student': student
        }
    )
    
# ==========================================
# PUBLIC ACTIVE FORMS
# ==========================================

@login_required
def public_active_forms(request):

    today = timezone.now().date()

    forms = DynamicForm.objects.filter(

        access_type='public',

        is_active=True,

        start_date__lte=today,

        deadline_date__gte=today
    )

    analytics = []

    for form in forms:

        total_responses = PublicFormResponse.objects.filter(

            form=form
        ).count()

        analytics.append({

            'form': form,

            'total_responses': total_responses,
        })

    return render(

        request,

        'accounts/public_active_forms.html',

        {

            'analytics': analytics,
        }
    )


# ==========================================
# PUBLIC FUTURE FORMS
# ==========================================

@login_required
def public_future_forms(request):

    today = timezone.now().date()

    forms = DynamicForm.objects.filter(

        access_type='public',

        start_date__gt=today
    )

    analytics = []

    for form in forms:

        total_responses = PublicFormResponse.objects.filter(

            form=form
        ).count()

        analytics.append({

            'form': form,

            'total_responses': total_responses,
        })

    return render(

        request,

        'accounts/public_upcoming_forms.html',

        {

            'analytics': analytics,
        }
    )


# ==========================================
# PUBLIC EXPIRED FORMS
# ==========================================

@login_required
def public_expired_forms(request):

    today = timezone.now().date()

    forms = DynamicForm.objects.filter(

        access_type='public',

        deadline_date__lt=today
    )

    analytics = []

    for form in forms:

        total_responses = PublicFormResponse.objects.filter(

            form=form
        ).count()

        analytics.append({

            'form': form,

            'total_responses': total_responses,
        })

    return render(

        request,

        'accounts/public_expired_forms.html',

        {

            'analytics': analytics,
        }
    )
# ==========================================
# PUBLIC FORMS DASHBOARD
# ==========================================

@login_required
def public_forms_dashboard(request):

    today = timezone.now().date()

    active_count = DynamicForm.objects.filter(

        access_type='public',

        is_active=True,

        start_date__lte=today,

        deadline_date__gte=today
    ).count()

    future_count = DynamicForm.objects.filter(

        access_type='public',

        start_date__gt=today
    ).count()

    expired_count = DynamicForm.objects.filter(

        access_type='public',

        deadline_date__lt=today
    ).count()

    context = {

        'active_count': active_count,

        'future_count': future_count,

        'expired_count': expired_count,
    }

    return render(

        request,

        'accounts/public_forms_dashboard.html',

        context
    )
    
# ==========================================
# TEACHER COMPLETED FORMS
# ==========================================
@login_required
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
    
@login_required
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


@login_required
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
    
    
@login_required
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
@login_required
@role_required('admin')
def edit_teacher(request, teacher_id):

    teacher = get_object_or_404(

        TeacherProfile.objects.select_related(
            'user'
        ),

        id=teacher_id
    )

    departments = Department.objects.all()

    sections = Section.objects.all()

    if request.method == 'POST':

        teacher.user.first_name = request.POST.get(
            'first_name'
        )

        teacher.user.last_name = request.POST.get(
            'last_name'
        )

        teacher.user.email = request.POST.get(
            'email'
        )

        teacher.user.save()

        teacher.department_id = request.POST.get(
            'department'
        )

        teacher.phone_number = request.POST.get(
            'phone_number'
        )

        teacher.save()

        selected_sections = request.POST.getlist(
            'assigned_sections'
        )

        teacher.assigned_sections.set(
            selected_sections
        )

        return redirect(
            'teachers_list'
        )

    context = {

        'teacher': teacher,

        'departments': departments,

        'sections': sections,
    }

    return render(

        request,

        'accounts/edit_teacher.html',

        context
    )


@login_required
@role_required('admin')
def delete_teacher(request, teacher_id):

    teacher = get_object_or_404(

        TeacherProfile.objects.select_related(
            'user'
        ),

        id=teacher_id
    )

    if request.method == 'POST':

        teacher.user.delete()

        return redirect(
            'teachers_list'
        )

    return render(

        request,

        'accounts/delete_teacher.html',

        {

            'teacher': teacher
        }
    )
@login_required
def add_teacher(request):

    departments = Department.objects.all()

    sections = Section.objects.all()

    # ==========================================
    # CREATE TEACHER
    # ==========================================

    if request.method == 'POST':

        username = request.POST.get(

            'username'
        )

        # ==========================================
        # DUPLICATE USERNAME CHECK
        # ==========================================

        if User.objects.filter(

            username=username

        ).exists():

            messages.error(

                request,

                'Teacher username already exists.'
            )

            context = {

                'departments': departments,

                'sections': sections
            }

            return render(

                request,

                'accounts/add_teacher.html',

                context
            )

        # ==========================================
        # CREATE USER
        # ==========================================

        user = User.objects.create_user(

            username=username,

            password=request.POST.get(
                'password'
            ),

            first_name=request.POST.get(
                'first_name'
            ),

            last_name=request.POST.get(
                'last_name'
            ),

            email=request.POST.get(
                'email'
            ),

            role='teacher'
        )

        # ==========================================
        # CREATE PROFILE
        # ==========================================

        teacher = TeacherProfile.objects.create(

            user=user,

            department_id=request.POST.get(
                'department'
            ),

            phone_number=request.POST.get(
                'phone_number'
            )
        )

        # ==========================================
        # ASSIGNED SECTIONS
        # ==========================================

        selected_sections = request.POST.getlist(

            'assigned_sections'
        )

        teacher.assigned_sections.set(

            selected_sections
        )

        # ==========================================
        # SUCCESS MESSAGE
        # ==========================================

        messages.success(

            request,

            'Teacher created successfully.'
        )

        return redirect(

            'teachers_list'
        )

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'departments': departments,

        'sections': sections
    }

    return render(

        request,

        'accounts/add_teacher.html',

        context
    )