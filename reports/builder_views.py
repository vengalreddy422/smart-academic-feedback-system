import json
from django.views.generic import View, TemplateView
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
import openpyxl
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from forms_engine.models import DynamicForm, FormQuestion, FormAnswer, PublicFormAnswer
from reports.services import get_allowed_forms_for_user, get_filtered_report_data
from reports.exports.identified.detailed_pdf import export_identified_detailed_pdf
from reports.exports.anonymous.detailed_pdf import export_anonymous_detailed_pdf

class ReportBuilderView(TemplateView):
    template_name = 'reports/builder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['forms'] = get_allowed_forms_for_user(self.request.user)
        else:
            context['forms'] = []
        context['selected_form_id'] = self.request.GET.get('form_id', '')
        return context


class LoadFieldsAJAXView(View):
    def get(self, request, *args, **kwargs):
        form_id = request.GET.get('form_id')
        if not form_id:
            return JsonResponse({'error': 'Missing form_id'}, status=400)
            
        form = get_object_or_404(DynamicForm, id=form_id)
        
        allowed_forms = get_allowed_forms_for_user(request.user)
        if not allowed_forms.filter(id=form_id).exists():
            return JsonResponse({'error': 'Unauthorized'}, status=403)
            
        questions = FormQuestion.objects.filter(form=form, is_system_field=False).order_by('order')
        
        fields_data = []
        for q in questions:
            options = []
            if q.field_type in ['select', 'radio', 'checkbox']:
                options = list(q.question_options.values_list('option_text', flat=True))
                
            fields_data.append({
                'id': q.id,
                'question': q.question,
                'field_type': q.field_type,
                'options': options
            })
            
        return JsonResponse({'fields': fields_data})


class PreviewReportAJAXView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
            
        form_id = data.get('form_id')
        filters = data.get('filters', [])
        page_num = data.get('page', 1)
        
        form = get_object_or_404(DynamicForm, id=form_id)
        
        allowed_forms = get_allowed_forms_for_user(request.user)
        if not allowed_forms.filter(id=form_id).exists():
            return JsonResponse({'error': 'Unauthorized'}, status=403)
            
        qs = get_filtered_report_data(form, request.user, filters)
        total_count = qs.count()
        
        paginator = Paginator(qs, 50)
        page_obj = paginator.get_page(page_num)
        
        is_public = form.access_type == 'public'
        is_anonymous = form.identity_type == 'anonymous'
        AnswerModel = PublicFormAnswer if is_public else FormAnswer
        
        # Pre-fetch answers for this page to avoid N+1 issues in preview
        if is_public:
            page_obj.object_list = page_obj.object_list.prefetch_related('publicformanswer_set')
        else:
            page_obj.object_list = page_obj.object_list.prefetch_related('formanswer_set', 'student__user')

        preview_questions = FormQuestion.objects.filter(form=form, is_system_field=False).order_by('order')[:5]
        
        rows = []
        for response in page_obj:
            row_dict = {}
            if not is_public and not is_anonymous:
                student = response.student
                user = student.user if student else None
                row_dict['Username'] = user.username if user else "N/A"
                row_dict['Name'] = f"{user.first_name} {user.last_name}" if user else "N/A"
                row_dict['Section'] = str(student.section) if student and student.section else "N/A"
            elif not is_public and is_anonymous:
                row_dict['Identity'] = "Anonymous"
            else:
                row_dict['Identity'] = "Public"
                
            # Quick answer lookup map for this response
            if is_public:
                answer_map = {ans.question_id: ans.answer for ans in response.publicformanswer_set.all()}
            else:
                answer_map = {ans.question_id: ans.answer for ans in response.formanswer_set.all()}
                
            for q in preview_questions:
                row_dict[q.question] = answer_map.get(q.id, "")
                
            rows.append(row_dict)
            
        headers = []
        if rows:
            headers = list(rows[0].keys())
        else:
            if not is_public and not is_anonymous:
                headers = ['Username', 'Name', 'Section']
            elif not is_public and is_anonymous:
                headers = ['Identity']
            else:
                headers = ['Identity']
            for q in preview_questions:
                headers.append(q.question)
        
        return JsonResponse({
            'total_count': total_count,
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'headers': headers,
            'rows': rows
        })


class DownloadReportView(View):
    def post(self, request, *args, **kwargs):
        # Allow both Form POST and JSON POST
        try:
            data = json.loads(request.body)
            form_id = data.get('form_id')
            filters = data.get('filters', [])
            export_format = data.get('format', 'excel')
        except json.JSONDecodeError:
            form_id = request.POST.get('form_id')
            filters = json.loads(request.POST.get('filters', '[]'))
            export_format = request.POST.get('format', 'excel')

        form = get_object_or_404(DynamicForm, id=form_id)
        
        allowed_forms = get_allowed_forms_for_user(request.user)
        if not allowed_forms.filter(id=form_id).exists():
            return HttpResponse('Unauthorized', status=403)
            
        qs = get_filtered_report_data(form, request.user, filters)
        
        is_public = form.access_type == 'public'
        is_anonymous = form.identity_type == 'anonymous'
        
        questions = FormQuestion.objects.filter(form=form).order_by('-is_system_field', 'order', 'id')
        clean_title = "".join([c if c.isalnum() else "_" for c in form.title])
        
        # PREFETCHING
        if is_public:
            qs = qs.prefetch_related('publicformanswer_set')
        else:
            qs = qs.prefetch_related('formanswer_set', 'student__user')

        # EXPORT LOGIC ROUTING
        if export_format == 'excel':
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Report"
            
            headers = []
            if not is_public and not is_anonymous:
                headers = ["Username", "First Name", "Last Name", "Section", "Department"]
                
            for q in questions:
                headers.append(q.question)
                
            if is_public:
                headers.append("Submitted At")
                
            ws.append(headers)

            for response in qs:
                row_data = []
                if not is_public and not is_anonymous:
                    student = response.student
                    user = student.user if student else None
                    row_data.extend([
                        user.username if user else "N/A",
                        user.first_name if user else "N/A",
                        user.last_name if user else "N/A",
                        str(student.section) if student and student.section else "N/A",
                        str(getattr(student, 'department', 'N/A'))
                    ])
                
                if is_public:
                    ans_map = {ans.question_id: ans.answer for ans in response.publicformanswer_set.all()}
                else:
                    ans_map = {ans.question_id: ans.answer for ans in response.formanswer_set.all()}

                for q in questions:
                    row_data.append(ans_map.get(q.id, ""))
                    
                if is_public:
                    row_data.append(response.submitted_at.strftime('%Y-%m-%d %H:%M:%S'))
                    
                ws.append(row_data)

            response_file = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response_file["Content-Disposition"] = f'attachment; filename="{clean_title}_report.xlsx"'
            wb.save(response_file)
            return response_file
            
        elif export_format == 'csv':
            response_file = HttpResponse(content_type='text/csv')
            response_file['Content-Disposition'] = f'attachment; filename="{clean_title}_report.csv"'
            writer = csv.writer(response_file)
            
            headers = []
            if not is_public and not is_anonymous:
                headers = ["Username", "First Name", "Last Name", "Section", "Department"]
            for q in questions:
                headers.append(q.question)
            if is_public:
                headers.append("Submitted At")
                
            writer.writerow(headers)
            
            for response in qs:
                row_data = []
                if not is_public and not is_anonymous:
                    student = response.student
                    user = student.user if student else None
                    row_data.extend([
                        user.username if user else "N/A",
                        user.first_name if user else "N/A",
                        user.last_name if user else "N/A",
                        str(student.section) if student and student.section else "N/A",
                        str(getattr(student, 'department', 'N/A'))
                    ])
                
                if is_public:
                    ans_map = {ans.question_id: ans.answer for ans in response.publicformanswer_set.all()}
                else:
                    ans_map = {ans.question_id: ans.answer for ans in response.formanswer_set.all()}

                for q in questions:
                    row_data.append(ans_map.get(q.id, ""))
                
                if is_public:
                    row_data.append(response.submitted_at.strftime('%Y-%m-%d %H:%M:%S'))
                    
                writer.writerow(row_data)
                
            return response_file

        elif export_format == 'pdf':
            # Use existing detailed pdf generators for private forms, custom for public
            if not is_public and not is_anonymous:
                # `export_identified_detailed_pdf` expects a specific layout, we reuse it.
                return export_identified_detailed_pdf(qs, f'{clean_title}_report')
            elif not is_public and is_anonymous:
                # `export_anonymous_detailed_pdf` expects a specific layout.
                return export_anonymous_detailed_pdf(qs, f'{clean_title}_report')
            else:
                # Public form PDF layout
                response_file = HttpResponse(content_type='application/pdf')
                response_file['Content-Disposition'] = f'attachment; filename="{clean_title}_report.pdf"'
                doc = SimpleDocTemplate(response_file, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                story = []
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, spaceAfter=20)
                record_header_style = ParagraphStyle('RecHead', parent=styles['Heading3'], fontSize=12, spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#2563eb'))
                q_style = ParagraphStyle('QuestText', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, spaceAfter=2, textColor=colors.HexColor('#0f172a'))
                a_style = ParagraphStyle('AnsText', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, spaceAfter=12, textColor=colors.HexColor('#334155'))

                story.append(Paragraph(f"{form.title} - Responses Report", title_style))
                for index, response in enumerate(qs, start=1):
                    timestamp = response.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
                    story.append(Paragraph(f"Submission #{index} — Date: {timestamp}", record_header_style))
                    ans_map = {ans.question_id: ans.answer for ans in response.publicformanswer_set.all()}
                    for question in questions:
                        user_answer = ans_map.get(question.id, '—')
                        story.append(Paragraph(f"<b>Q: {question.question}</b>", q_style))
                        story.append(Paragraph(f"{user_answer}", a_style))
                    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceBefore=5, spaceAfter=20))
                doc.build(story)
                return response_file

        return HttpResponse("Invalid format", status=400)
