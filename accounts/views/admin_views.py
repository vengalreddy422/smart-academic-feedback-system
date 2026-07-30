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
from django.core.paginator import Paginator
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
                return redirect('login')
            user_role = getattr(request.user, 'role', None)
            if user_role not in roles:
                return HttpResponse('Unauthorized', status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


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

    users_list = User.objects.all().order_by('-id')
    paginator = Paginator(users_list, 50)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)

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

    teachers_queryset = teachers.order_by('-id')
    paginator = Paginator(teachers_queryset, 50)
    page_number = request.GET.get('page')
    teachers_page = paginator.get_page(page_number)

    return render(

        request,

        'accounts/teachers_list.html',

        {

            'teachers': teachers_page,
        }
    )

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
    # ORDERING & PAGINATION
    # ==========================================

    students_queryset = students.order_by(
        'department__name',
        'section__name',
        'roll_number'
    )

    paginator = Paginator(students_queryset, 50)
    page_number = request.GET.get('page')
    students_page = paginator.get_page(page_number)

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {
        'students': students_page
    }

    return render(

        request,

        'accounts/students_list.html',

        context
    )

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
