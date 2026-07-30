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