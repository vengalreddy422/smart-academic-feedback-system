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


    # ==============================================================================
    # EXCEL GENERATION LOGIC
    # ==============================================================================
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Form Summary"

    # Fetch ALL dynamic questions belonging to this specific form
    questions = FormQuestion.objects.filter(form=form).order_by(
        '-is_system_field', 
        'order', 
        'id'
    )

    # Construct clean headers without time fields
    headers = ["Username", "Section", "Department"]
    for q in questions:
        headers.append(q.question)
        
    ws.append(headers)

    # Populate rows for each student submission inside the filtered queryset
    for response_obj in queryset:
        student = response_obj.student
        user = student.user if student else None
        
        # Base metadata row data (Username, Section, Department only)
        row_data = [
            user.username if user else "N/A",
            str(student.section) if student and student.section else "N/A",  # ◄── CHANGED TO THIS
            str(getattr(student, 'department', 'N/A'))
        ]

        # Sequentially map values for ALL questions without skipping anything
        for q in questions:
            # Match against your exact field definitions: 'question' and 'response'
            answer_obj = FormAnswer.objects.filter(question=q, response=response_obj).first()
            if answer_obj and answer_obj.answer:
                row_data.append(answer_obj.answer)
            else:
                row_data.append("")  # Leaves a blank space in Excel if skipped

        ws.append(row_data)

    # Package file as a seamless sheet stream back to the user's browser
    clean_title = "".join([c if c.isalnum() else "_" for c in form.title])
    
    excel_response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    excel_response["Content-Disposition"] = f'attachment; filename="{clean_title}_summary.xlsx"'
    
    wb.save(excel_response)
    return excel_response
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

    return export_identified_detailed_pdf(

        queryset,

        f'{form.title}_detailed'
    )


    
from django.http import HttpResponse
import csv


# ==========================================
# PUBLIC FORM EXCEL EXPORT
# ==========================================

def public_form_excel(
    request,
    form_id
):

    form = get_object_or_404(

        DynamicForm,
        id=form_id
    )

    responses = PublicFormResponse.objects.filter(
        form=form
    )

    workbook = Workbook()

    worksheet = workbook.active

    worksheet.title = 'Public Responses'

    # ==========================================
    # DYNAMIC QUESTIONS
    # ==========================================

    questions = FormQuestion.objects.filter(

    form=form

).order_by(

    '-is_system_field',

    'order',

    'id'
)

    headers = []

    for question in questions:

        headers.append(
            question.question
        )

    headers.append(
        'Submitted At'
    )

    worksheet.append(headers)

    # ==========================================
    # RESPONSE ROWS
    # ==========================================

    for response in responses:

        row = []

        answers = PublicFormAnswer.objects.filter(
            response=response
        )

        answer_map = {}

        for answer in answers:

            answer_map[
                answer.question.id
            ] = answer.answer

        for question in questions:

            row.append(

                answer_map.get(
                    question.id,
                    ''
                )
            )

        row.append(
            str(response.submitted_at)
        )

        worksheet.append(row)

    response_file = HttpResponse(

        content_type=
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response_file[
        'Content-Disposition'
    ] = f'attachment; filename={form.title}.xlsx'

    workbook.save(response_file)

    return response_file
# ==========================================
# PUBLIC DETAILED PDF
# ==========================================

def public_detailed_pdf(
    request,
    form_id
):

    form = get_object_or_404(

        DynamicForm,
        id=form_id
    )

    queryset = (
        PublicFormResponse.objects
        .filter(form=form)
        .prefetch_related(
            'publicformanswer_set__question'
        )
    )

    return export_anonymous_detailed_pdf(

        queryset,

        f'{form.title}_public_detailed'
    )
    
# ==========================================
# PRIVATE ANONYMOUS PDF
# ==========================================
# ==========================================
# PRIVATE ANONYMOUS PDF
# ==========================================

# ==========================================
# PRIVATE ANONYMOUS PDF
# ==========================================

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

    queryset = (

        FormResponse.objects
        .filter(
            form=form
        )
        .prefetch_related(
            'formanswer_set__question'
        )
    )

    return export_anonymous_detailed_pdf(

        queryset,

        f'{form.title}_private_anonymous'
    )
# ==========================================
# PRIVATE ANONYMOUS EXCEL
# ==========================================

# ==========================================
# PRIVATE ANONYMOUS EXCEL
# ==========================================
import openpyxl
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

# Crucial: Import your models from your main forms engine app folder
# (Replace 'forms_engine' with 'forms' or 'dynamic_forms' if your folder name is different)
from forms_engine.models import DynamicForm, FormQuestion, FormResponse, FormAnswer
from accounts.models import TeacherProfile

# ==============================================================================
# 1. IDENTIFIED EXCEL DOWNLOAD (Shows Username, Section, Department)
# ==============================================================================
@login_required
def identified_summary_excel(request, form_id):
    form = get_object_or_404(DynamicForm, id=form_id)

    # Admin Filter
    if request.user.role == 'admin':
        queryset = FormResponse.objects.filter(form=form).select_related(
            'student', 'student__user', 'form'
        )
    # Teacher Filter
    elif request.user.role == 'teacher':
        teacher_profile = get_object_or_404(TeacherProfile, user=request.user)
        assigned_sections = teacher_profile.assigned_sections.all()
        queryset = FormResponse.objects.filter(
            form=form, student__section__in=assigned_sections
        ).select_related('student', 'student__user', 'form')
    else:
        return HttpResponse('Unauthorized', status=403)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Identified Summary"

    # Fetch questions ordered perfectly
    questions = FormQuestion.objects.filter(form=form).order_by(
        '-is_system_field', 'order', 'id'
    )

    # Headers with user information columns
    headers = ["Username", "Section", "Department"]
    for q in questions:
        headers.append(q.question)
    ws.append(headers)

    # Populate Rows
    for response_obj in queryset:
        student = response_obj.student
        user = student.user if student else None
        
        # Safe text strings prevent Excel conversion values crashes
        row_data = [
            user.username if user else "N/A",
            str(student.section) if student and student.section else "N/A",
            str(getattr(student, 'department', 'N/A'))
        ]

        for q in questions:
            answer_obj = FormAnswer.objects.filter(question=q, response=response_obj).first()
            if answer_obj and answer_obj.answer:
                row_data.append(answer_obj.answer)
            else:
                row_data.append("")

        ws.append(row_data)

    clean_title = "".join([c if c.isalnum() else "_" for c in form.title])
    excel_response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    excel_response["Content-Disposition"] = f'attachment; filename="{clean_title}_identified_summary.xlsx"'
    wb.save(excel_response)
    return excel_response


# ==============================================================================
# 2. PRIVATE ANONYMOUS EXCEL DOWNLOAD (Hides ALL Identity, No Time Field)
# ==============================================================================
@login_required
def private_anonymous_excel(request, form_id):
    form = get_object_or_404(DynamicForm, id=form_id)
    responses = FormResponse.objects.filter(form=form)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Anonymous Responses'

    # Fetch questions ordered perfectly
    questions = FormQuestion.objects.filter(form=form).order_by(
        '-is_system_field', 'order', 'id'
    )

    # Headers contain ONLY questions to protect student anonymity
    headers = []
    for question in questions:
        headers.append(question.question)
    ws.append(headers)

    # Populate rows without any identity references
    for response in responses:
        row = []
        for question in questions:
            answer = FormAnswer.objects.filter(response=response, question=question).first()
            
            # Checks that object exists AND contains non-empty data safely
            if answer and answer.answer:
                row.append(answer.answer)
            else:
                row.append('')

        ws.append(row)

    clean_title = "".join([c if c.isalnum() else "_" for c in form.title])
    response_file = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response_file['Content-Disposition'] = f'attachment; filename={clean_title}_anonymous.xlsx'
    wb.save(response_file)
    return response_file