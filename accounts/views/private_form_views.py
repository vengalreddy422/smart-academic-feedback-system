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