import openpyxl

from django.http import HttpResponse

from openpyxl.styles import Font


def export_identified_summary_excel(
    queryset,
    filename
):

    workbook = openpyxl.Workbook()

    worksheet = workbook.active

    worksheet.title = 'Summary Report'

    headers = [

        'First Name',
        'Email',
        'Form Name',
        'Status',
        'Submitted Date'

    ]

    worksheet.append(headers)

    for cell in worksheet[1]:

        cell.font = Font(bold=True)

    for response in queryset:

        worksheet.append([

            response.student.user.first_name,

            response.student.user.email,

            response.form.title,

            'Completed',

            str(response.submitted_at)

        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response[
        'Content-Disposition'
    ] = f'attachment; filename={filename}.xlsx'

    workbook.save(response)

    return response