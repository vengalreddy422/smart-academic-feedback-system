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
@login_required
def identified_summary_excel(
    request,
    form_id
):

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

        return HttpResponse(
            'Unauthorized'
        )

    return export_identified_summary_excel(

        queryset,

        f'{form.title}_summary'
    )

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

@login_required
def private_anonymous_excel(
    request,
    form_id
):

    form = get_object_or_404(

        DynamicForm,
        id=form_id
    )

    responses = FormResponse.objects.filter(

        form=form

    )

    workbook = Workbook()

    worksheet = workbook.active

    worksheet.title = (

        'Anonymous Responses'
    )

    # ==========================================
    # QUESTIONS
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

    worksheet.append(

        headers
    )

    # ==========================================
    # RESPONSE DATA
    # ==========================================

    for response in responses:

        row = []

        for question in questions:

            answer = FormAnswer.objects.filter(

                response=response,

                question=question

            ).first()

            if answer:

                row.append(

                    answer.answer
                )

            else:

                row.append(

                    ''
                )

        row.append(

            str(
                response.submitted_at
            )
        )

        worksheet.append(

            row
        )

    response_file = HttpResponse(

        content_type=
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response_file[
        'Content-Disposition'
    ] = (

        f'attachment; filename={form.title}_anonymous.xlsx'
    )

    workbook.save(

        response_file
    )

    return response_file