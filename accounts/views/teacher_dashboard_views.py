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