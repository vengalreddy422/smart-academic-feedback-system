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