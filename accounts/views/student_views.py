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
                return redirect('login')
            user_role = getattr(request.user, 'role', None)
            if user_role not in roles:
                return HttpResponse('Unauthorized', status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@role_required('student')
def student_dashboard(request):

    # ==========================================
    # STUDENT PROFILE
    # ==========================================

    student_profile = get_object_or_404(

        StudentProfile,

        user=request.user
    )

    # ==========================================
    # TODAY DATE
    # ==========================================

    today = timezone.now().date()

    # ==========================================
    # ONLY PRIVATE ACTIVE FORMS
    # ==========================================

    all_forms = DynamicForm.objects.filter(

        access_type='private',

        is_active=True

    ).distinct()

    # ==========================================
    # SUBMITTED FORM IDS
    # ==========================================

    submitted_form_ids = FormResponse.objects.filter(
        student=student_profile,
        status='submitted'
    ).values_list(
        'form_id',
        flat=True
    )

    # ==========================================
    # PENDING / ACTIVE FORMS
    # ==========================================

    pending_forms = all_forms.filter(

        start_date__lte=today,

        deadline_date__gte=today

    ).exclude(

        id__in=submitted_form_ids
    )

    # ==========================================
    # UPCOMING FORMS
    # ==========================================

    upcoming_forms = all_forms.filter(

        start_date__gt=today

    ).exclude(

        id__in=submitted_form_ids
    )

    # ==========================================
    # COMPLETED FORMS
    # ==========================================

    completed_forms = all_forms.filter(

    id__in=submitted_form_ids,

    
)

    # ==========================================
    # EXPIRED FORMS
    # ==========================================

    expired_forms = all_forms.filter(

        deadline_date__lt=today

    ).exclude(

        id__in=submitted_form_ids
    )

    # ==========================================
    # COUNTS
    # ==========================================

    total_forms_count = all_forms.count()

    pending_forms_count = pending_forms.count()

    upcoming_forms_count = upcoming_forms.count()

    completed_forms_count = completed_forms.count()

    expired_forms_count = expired_forms.count()

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'student_profile': student_profile,

        # ======================================
        # FORM LISTS
        # ======================================

        'pending_forms': pending_forms,

        'upcoming_forms': upcoming_forms,

        'completed_forms': completed_forms,

        'expired_forms': expired_forms,

        # ======================================
        # COUNTS
        # ======================================

        'total_forms_count': total_forms_count,

        'pending_forms_count': pending_forms_count,

        'upcoming_forms_count': upcoming_forms_count,

        'completed_forms_count': completed_forms_count,

        'expired_forms_count': expired_forms_count,
    }

    # ==========================================
    # RENDER TEMPLATE
    # ==========================================

    return render(

        request,

        'accounts/student_dashboard.html',

        context
    )

def user_logout(request):

    logout(request)

    return redirect(
        reverse('login')
    )


from django.contrib.auth.views import PasswordChangeView

from django.contrib.auth import update_session_auth_hash

from django.urls import reverse_lazy


from django.contrib.auth.views import PasswordChangeView

from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth import update_session_auth_hash

from django.urls import reverse_lazy


class UserPasswordChangeView(

    LoginRequiredMixin,

    PasswordChangeView

):

    template_name = 'accounts/password_change.html'

    success_url = reverse_lazy('student_dashboard')

    def form_valid(self, form):

        response = super().form_valid(form)

        # KEEP USER LOGGED IN

        update_session_auth_hash(

            self.request,

            form.user

        )

        return response

@role_required('student')
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

@role_required('student')
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

@role_required('student')
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

@role_required('student')
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
