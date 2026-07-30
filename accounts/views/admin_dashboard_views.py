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

    total_private_responses = (
        FormResponse.objects.count()
    )

    total_public_responses = (
        PublicFormResponse.objects.count()
    )

    total_responses = (
        total_private_responses
        + total_public_responses
    )

    # ==========================================
    # RECENT FORMS
    # ==========================================

    recent_forms = (
        DynamicForm.objects.order_by(
            '-created_at'
        )[:5]
    )

    # ==========================================
    # RECENT STUDENTS
    # ==========================================

    recent_students = (
        StudentProfile.objects.select_related(
            'user'
        ).order_by(
            '-id'
        )[:5]
    )

    # ==========================================
    # RECENT TEACHERS
    # ==========================================

    recent_teachers = (
        TeacherProfile.objects.select_related(
            'user'
        ).order_by(
            '-id'
        )[:5]
    )

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