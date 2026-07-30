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