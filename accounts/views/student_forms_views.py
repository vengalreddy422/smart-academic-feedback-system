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


def completed_forms(request):

    student_profile = get_object_or_404(

        StudentProfile,

        user=request.user
    )

    submitted_form_ids = FormResponse.objects.filter(
        student=student_profile,
        status='submitted'
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
        student=student_profile,
        status='submitted'
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
        student=student_profile,
        status='submitted'
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

def expired_forms(request):

    student_profile = get_object_or_404(

        StudentProfile,


        user=request.user
    )

    today = timezone.now().date()

    submitted_form_ids = FormResponse.objects.filter(
        student=student_profile,
        status='submitted'
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