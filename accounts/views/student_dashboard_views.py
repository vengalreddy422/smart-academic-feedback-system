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