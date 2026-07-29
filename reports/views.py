from urllib import request

from django.shortcuts import get_object_or_404

from openpyxl import Workbook
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib import styles

from accounts.models import (
    TeacherProfile,
    StudentProfile
)


from forms_engine.models import (
    DynamicForm,
    FormQuestion,
    FormResponse,
    FormAnswer,
    PublicFormResponse,
    PublicFormAnswer
)
from reports.exports.identified.summary_excel import (
    export_identified_summary_excel
)

from reports.exports.identified.detailed_pdf import (
    export_identified_detailed_pdf
)



from reports.exports.anonymous.detailed_pdf import (
    export_anonymous_detailed_pdf
)


# ==========================================
# IDENTIFIED SUMMARY EXCEL
# ==========================================
import openpyxl
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

# 1. IMPORT MODELS FROM YOUR FORMS ENGINE APPLICATION
# (Change 'forms_engine' to your exact forms app folder name if it's named 'forms' or 'dynamic_forms')
from forms_engine.models import DynamicForm, FormQuestion, FormResponse, FormAnswer
from accounts.models import TeacherProfile

@login_required
def identified_summary_excel(request, form_id):
    form = get_object_or_404(
        DynamicForm,
        id=form_id
    )

    # ==========================================
    # ADMIN
    # ==========================================
    if request.user.role == 'admin':
        queryset = FormResponse.objects.filter(
            form=form
        ).select_related(
            'student',
            'student__user',
            'form'
        )

    # ==========================================
    # TEACHER
    # ==========================================
    elif request.user.role == 'teacher':
        teacher_profile = get_object_or_404(
            TeacherProfile,
            user=request.user
        )

        assigned_sections = (
            teacher_profile.assigned_sections.all()
        )

        queryset = FormResponse.objects.filter(
            form=form,
            student__section__in=assigned_sections
        ).select_related(
            'student',
            'student__user',
            'form'
        )

    # ==========================================
    # OTHER USERS
    # ==========================================
    else:
        return HttpResponse('Unauthorized', status=403)


    from reports.export_utils import generate_dynamic_excel
    questions = FormQuestion.objects.filter(form=form).order_by(
        '-is_system_field', 
        'order', 
        'id'
    )
    clean_title = "".join([c if c.isalnum() else "_" for c in form.title])
    return generate_dynamic_excel(form, queryset, questions, f"{clean_title}_summary")
# ==========================================
# IDENTIFIED DETAILED PDF
# ==========================================

@login_required
def identified_detailed_pdf(
    request,
    form_id
):

    form = get_object_or_404(
        DynamicForm,
        id=form_id
    )

    # ==========================================
    # ADMIN USER
    # ==========================================

    if request.user.role == 'admin':

        queryset = FormResponse.objects.filter(

            form=form

        ).select_related(

            'student',
            'student__user',
            'form'
        )

    # ==========================================
    # TEACHER USER
    # ==========================================

    elif request.user.role == 'teacher':

        teacher_profile = get_object_or_404(

            TeacherProfile,

            user=request.user
        )

        assigned_sections = (
            teacher_profile.assigned_sections.all()
        )

        queryset = FormResponse.objects.filter(

            form=form,

            student__section__in=assigned_sections

        ).select_related(

            'student',
            'student__user',
            'form'
        )

    # ==========================================
    # OTHER USERS
    # ==========================================

    else:

        return HttpResponse(
            'Unauthorized'
        )

    from reports.export_utils import generate_dynamic_pdf
    questions = FormQuestion.objects.filter(form=form).order_by(
        '-is_system_field', 
        'order', 
        'id'
    )
    clean_title = "".join([c if c.isalnum() else "_" for c in form.title])
    return generate_dynamic_pdf(form, queryset, questions, f'{clean_title}_detailed')


    
from django.http import HttpResponse
import csv


# ==========================================
# PUBLIC FORM EXCEL EXPORT
# ==========================================

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from openpyxl import Workbook

# ReportLab imports needed for the PDF layout generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. EXCEL EXPORT (Horizontal Rows)
# ==========================================
def public_form_excel(request, form_id):
    form = get_object_or_404(DynamicForm, id=form_id)
    
    responses = PublicFormResponse.objects.filter(form=form).prefetch_related('publicformanswer_set')
    questions = FormQuestion.objects.filter(form=form).order_by('-is_system_field', 'order', 'id')
    
    from reports.export_utils import generate_dynamic_excel
    clean_title = "".join([c if c.isalnum() else "_" for c in form.title])
    return generate_dynamic_excel(form, responses, questions, clean_title)

# ==========================================
# 2. PDF EXPORT (Vertical Sequential Records)
# ==========================================
def public_detailed_pdf(request, form_id):
    form = get_object_or_404(DynamicForm, id=form_id)
    responses = PublicFormResponse.objects.filter(form=form).prefetch_related('publicformanswer_set')
    questions = FormQuestion.objects.filter(form=form).order_by('-is_system_field', 'order', 'id')

    from reports.export_utils import generate_dynamic_pdf
    clean_title = "".join([c if c.isalnum() else "_" for c in form.title])
    return generate_dynamic_pdf(form, responses, questions, clean_title)
# ==========================================
# PRIVATE ANONYMOUS PDF
# ==========================================

@login_required
def private_anonymous_pdf(
    request,
    form_id
):

    form = get_object_or_404(

        DynamicForm,
        id=form_id
    )

        # ==========================================
    # ADMIN USER
    # ==========================================

    if request.user.role == 'admin':

        queryset = (
            FormResponse.objects
            .filter(
                form=form
            )
            .prefetch_related(
                'formanswer_set__question'
            )
        )

    # ==========================================
    # TEACHER USER
    # ==========================================

    elif request.user.role == 'teacher':

        teacher_profile = get_object_or_404(
            TeacherProfile,
            user=request.user
        )

        assigned_sections = (
            teacher_profile.assigned_sections.all()
        )

        queryset = (
            FormResponse.objects
            .filter(
                form=form,
                student__section__in=assigned_sections
            )
            .prefetch_related(
                'formanswer_set__question'
            )
        )

    # ==========================================
    # OTHER USERS
    # ==========================================

    else:

        return HttpResponse(
            'Unauthorized',
            status=403
        )

    from reports.export_utils import generate_dynamic_pdf
    questions = FormQuestion.objects.filter(form=form).order_by(
        '-is_system_field', 
        'order', 
        'id'
    )
    clean_title = "".join([c if c.isalnum() else "_" for c in form.title])
    return generate_dynamic_pdf(form, queryset, questions, f'{clean_title}_private_anonymous')


# ==========================================
# PRIVATE ANONYMOUS EXCEL
# =========================================
# Crucial: Import your models from your main forms engine app folder
# (Replace 'forms_engine' with 'forms' or 'dynamic_forms' if your folder name is different)
from forms_engine.models import DynamicForm, FormQuestion, FormResponse, FormAnswer
from accounts.models import TeacherProfile

# ==============================================================================
# 2. PRIVATE ANONYMOUS EXCEL DOWNLOAD (Hides ALL Identity, No Time Field)
# ==============================================================================
@login_required
def private_anonymous_excel(request, form_id):
    form = get_object_or_404(DynamicForm, id=form_id)
    
    # ==========================================
    # ADMIN USER
    # ==========================================
    if request.user.role == 'admin':
        responses = FormResponse.objects.filter(form=form)
    # ==========================================
    # TEACHER USER
    # ==========================================
    elif request.user.role == 'teacher':
        teacher_profile = get_object_or_404(TeacherProfile, user=request.user)
        assigned_sections = teacher_profile.assigned_sections.all()
        responses = FormResponse.objects.filter(form=form, student__section__in=assigned_sections)
    else:
        return HttpResponse('Unauthorized', status=403)

    questions = FormQuestion.objects.filter(form=form).order_by(
        '-is_system_field', 'order', 'id'
    )

    from reports.export_utils import generate_dynamic_excel
    clean_title = "".join([c if c.isalnum() else "_" for c in form.title])
    return generate_dynamic_excel(form, responses, questions, f'{clean_title}_anonymous')