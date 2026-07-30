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