from urllib import request
from django.shortcuts import get_object_or_404
from openpyxl import Workbook
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import styles
from accounts.models import TeacherProfile, StudentProfile
from forms_engine.models import DynamicForm, FormQuestion, FormResponse, FormAnswer, PublicFormResponse, PublicFormAnswer
import openpyxl


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
