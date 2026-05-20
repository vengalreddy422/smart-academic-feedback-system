from django.http import HttpResponse

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

from reportlab.lib.pagesizes import A4

from reports.utils import (
    build_anonymous_answers
)


def export_anonymous_detailed_pdf(
    queryset,
    filename
):

    response = HttpResponse(
        content_type='application/pdf'
    )

    response[
        'Content-Disposition'
    ] = f'attachment; filename={filename}.pdf'

    document = SimpleDocTemplate(
        response,
        pagesize=A4
    )

    elements = []

    styles = getSampleStyleSheet()

    # ==========================================
    # ALL RESPONSES
    # ==========================================

    for response_obj in queryset:

        elements.append(

            Paragraph(
                '<b>Anonymous Response</b>',
                styles['Heading2']
            )

        )

        elements.append(

            Paragraph(
                f'<b>Submitted At :</b> {response_obj.submitted_at}',
                styles['BodyText']
            )

        )

        elements.append(Spacer(1, 15))

        # ==========================================
        # ANSWERS
        # ==========================================

        answers = build_anonymous_answers(
            response_obj
        )

        for question, answer in answers.items():

            elements.append(

                Paragraph(
                    f'<b>{question}</b> : {answer}',
                    styles['BodyText']
                )

            )

            elements.append(Spacer(1, 6))

        elements.append(Spacer(1, 25))

    document.build(elements)

    return response