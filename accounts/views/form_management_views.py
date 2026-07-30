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


@role_required('admin')
def private_forms(request):

    # ==========================================
    # TODAY
    # ==========================================

    today = timezone.now().date()

    # ==========================================
    # PRIVATE FORMS
    # ==========================================

    forms = DynamicForm.objects.filter(
        access_type='private'
    )

    # ==========================================
    # TOTAL STUDENTS (GET ONCE)
    # ==========================================

    total_students = (
        StudentProfile.objects.count()
    )

    # ==========================================
    # GET ALL FORM RESPONSES ONCE
    # ==========================================

    responses = FormResponse.objects.filter(
        form__in=forms
    ).values(
        'form_id',
        'student_id'
    )

    # ==========================================
    # GROUP STUDENTS BY FORM
    # ==========================================

    submitted_by_form = {}

    for response in responses:

        form_id = response['form_id']

        student_id = response[
            'student_id'
        ]

        if form_id not in submitted_by_form:

            submitted_by_form[
                form_id
            ] = set()

        submitted_by_form[
            form_id
        ].add(student_id)

    # ==========================================
    # ANALYTICS
    # ==========================================

    analytics = []

    for form in forms:

        submitted_ids = (
            submitted_by_form.get(
                form.id,
                set()
            )
        )

        submitted_count = len(
            submitted_ids
        )

        pending_count = (
            total_students
            - submitted_count
        )

        # ======================================
        # ANONYMOUS FORM
        # ======================================

        if form.identity_type == 'anonymous':

            analytics.append({

                'form': form,

                'total_students':
                    total_students,

                'submitted_count':
                    submitted_count,

                'pending_count':
                    pending_count,

                'students': [],

                'is_anonymous':
                    True
            })

        # ======================================
        # IDENTIFIED FORM
        # ======================================

        else:

            submitted_students = (
                StudentProfile.objects.filter(
                    id__in=submitted_ids
                )
                .select_related(
                    'user',
                    'department',
                    'section'
                )
            )

            analytics.append({

                'form': form,

                'total_students':
                    total_students,

                'submitted_count':
                    submitted_count,

                'pending_count':
                    pending_count,

                'students':
                    submitted_students,

                'is_anonymous':
                    False
            })

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'analytics':
            analytics,

        'today':
            today
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
def public_form_qr(request, form_id):

    if request.user.role != 'admin':

        return HttpResponse(
            'Unauthorized'
        )

    form = get_object_or_404(

        DynamicForm,

        id=form_id
    )

    public_url = (

        f'https://feedback-system-s3ty.onrender.com'
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

@role_required('admin')

def add_question(request, form_id):

    form = get_object_or_404(
        DynamicForm,
        id=form_id
    )

    from forms_engine.field_registry import FIELD_REGISTRY

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
            placeholder=request.POST.get('placeholder', ''),
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

        if FIELD_REGISTRY.get(field_type, {}).get('needs_options', False):
            options_list = request.POST.getlist('options')
            for option in options_list:
                if option.strip():
                    QuestionOption.objects.create(question=question, option_text=option.strip())

        # ==========================================
        # CONDITIONAL LOGIC
        # ==========================================
        from forms_engine.models import FormQuestionCondition, FormResponse, PublicFormResponse
        parent_question_id = request.POST.get('parent_question')
        if parent_question_id:
            try:
                parent_question = FormQuestion.objects.get(id=parent_question_id, form=form)
                if parent_question.id != question.id:
                    FormQuestionCondition.objects.create(
                        question=question,
                        parent_question=parent_question,
                        operator=request.POST.get('operator', 'equals'),
                        trigger_value=request.POST.get('trigger_value', ''),
                        action=request.POST.get('action', 'show')
                    )
            except FormQuestion.DoesNotExist:
                # Invalid parent question id or belongs to another form
                pass

        # ==========================================
        # VERSION BUMP
        # ==========================================
        form.version += 1
        form.save(update_fields=['version'])
        
        FormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')
        PublicFormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')

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
    
    existing_questions = FormQuestion.objects.filter(form=form).order_by('order')

    return render(

        request,

        'accounts/add_question.html',

        {
            'form': form,
            'field_registry': FIELD_REGISTRY,
            'existing_questions': existing_questions,
        }
    )

from django.http import JsonResponse

@role_required('admin')
def get_form_questions(request, form_id):
    form = get_object_or_404(DynamicForm, id=form_id)
    questions = FormQuestion.objects.filter(form=form).order_by('order')
    
    data = []
    for q in questions:
        if not q.is_system_field:
            data.append({
                'id': q.id,
                'question': q.question,
                'field_type_display': q.get_field_type_display(),
            })
            
    return JsonResponse({'questions': data})

@role_required('admin')

def delete_question(request, question_id):

    question = get_object_or_404(

        FormQuestion,

        id=question_id
    )

    form_id = question.form.id
    form = question.form

    question.delete()

    from forms_engine.models import FormResponse, PublicFormResponse
    form.version += 1
    form.save(update_fields=['version'])
    FormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')
    PublicFormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')

    return redirect('edit_form', form_id=form_id)

@role_required('admin')

def delete_option(request, option_id):

    option = get_object_or_404(

        QuestionOption,

        id=option_id
    )

    form_id = option.question.form.id
    form = option.question.form

    option.delete()

    from forms_engine.models import FormResponse, PublicFormResponse
    form.version += 1
    form.save(update_fields=['version'])
    FormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')
    PublicFormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')

    return redirect('edit_form', form_id=form_id)

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
