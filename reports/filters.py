import json
from datetime import datetime
import logging

from django.db.models import Q, FloatField, DateField
from django.db.models.functions import Cast
from forms_engine.models import FormResponse, FormAnswer, PublicFormResponse, PublicFormAnswer
from accounts.models import TeacherProfile

logger = logging.getLogger(__name__)

class FormReportFilterEngine:
    """
    Engine to dynamically filter FormResponse and PublicFormResponse records
    based on EAV (Entity-Attribute-Value) answers.
    """

    @classmethod
    def get_scoped_responses(cls, form, user):
        """
        Returns the base queryset scoped by the user's role.
        """
        if form.access_type == 'public':
            return PublicFormResponse.objects.filter(form=form)

        qs = FormResponse.objects.filter(form=form)
        if user.role == 'teacher':
            try:
                teacher_profile = TeacherProfile.objects.get(user=user)
                assigned_sections = teacher_profile.assigned_sections.all()
                qs = qs.filter(student__section__in=assigned_sections)
            except TeacherProfile.DoesNotExist:
                qs = qs.none()
        elif user.role != 'admin':
            qs = qs.none()
            
        return qs

    @classmethod
    def apply_filters(cls, form, user, filter_params):
        """
        Apply a set of filters to the scoped responses.
        """
        qs = cls.get_scoped_responses(form, user)

        if not filter_params:
            return qs

        is_public = form.access_type == 'public'
        AnswerModel = PublicFormAnswer if is_public else FormAnswer

        for param in filter_params:
            question_id = param.get('question_id')
            field_type = param.get('field_type')
            operator = param.get('operator')
            value = param.get('value')
            value2 = param.get('value2')

            if not question_id or value is None or value == '':
                continue

            ans_qs = AnswerModel.objects.filter(question_id=question_id)

            if field_type in ['text', 'textarea', 'email']:
                if operator == 'contains':
                    ans_qs = ans_qs.filter(answer__icontains=value)
                elif operator == 'startswith':
                    ans_qs = ans_qs.filter(answer__istartswith=value)
                elif operator == 'endswith':
                    ans_qs = ans_qs.filter(answer__iendswith=value)
                elif operator == 'equals':
                    ans_qs = ans_qs.filter(answer__iexact=value)
                else:
                    ans_qs = ans_qs.filter(answer__icontains=value)

            elif field_type in ['select', 'radio']:
                ans_qs = ans_qs.filter(answer__iexact=value)

            elif field_type == 'checkbox':
                # OR logic for multiple options within the same checkbox field
                if isinstance(value, list) and value:
                    q_objects = Q()
                    for val in value:
                        q_objects |= Q(answer__icontains=val)
                    ans_qs = ans_qs.filter(q_objects)
                elif isinstance(value, str):
                    ans_qs = ans_qs.filter(answer__icontains=value)

            elif field_type in ['number', 'rating']:
                # Filter out invalid numeric strings before casting
                ans_qs = ans_qs.filter(answer__regex=r'^-?\d+(\.\d+)?$')
                ans_qs = ans_qs.annotate(as_num=Cast('answer', output_field=FloatField()))
                
                try:
                    num_val = float(value)
                    if operator == '>':
                        ans_qs = ans_qs.filter(as_num__gt=num_val)
                    elif operator == '>=':
                        ans_qs = ans_qs.filter(as_num__gte=num_val)
                    elif operator == '<':
                        ans_qs = ans_qs.filter(as_num__lt=num_val)
                    elif operator == '<=':
                        ans_qs = ans_qs.filter(as_num__lte=num_val)
                    elif operator == '=':
                        ans_qs = ans_qs.filter(as_num=num_val)
                    elif operator == 'between' and value2:
                        num_val2 = float(value2)
                        ans_qs = ans_qs.filter(as_num__gte=num_val, as_num__lte=num_val2)
                except ValueError as e:
                    logger.warning(f"Invalid number filter value: {value}. Error: {e}")
                    continue

            elif field_type == 'date':
                # Filter out invalid date strings before casting
                ans_qs = ans_qs.filter(answer__regex=r'^\d{4}-\d{2}-\d{2}$')
                ans_qs = ans_qs.annotate(as_date=Cast('answer', output_field=DateField()))
                
                try:
                    date_val = datetime.strptime(str(value), '%Y-%m-%d').date()
                    if operator == 'before':
                        ans_qs = ans_qs.filter(as_date__lt=date_val)
                    elif operator == 'after':
                        ans_qs = ans_qs.filter(as_date__gt=date_val)
                    elif operator == 'between' and value2:
                        date_val2 = datetime.strptime(str(value2), '%Y-%m-%d').date()
                        ans_qs = ans_qs.filter(as_date__gte=date_val, as_date__lte=date_val2)
                except ValueError as e:
                    logger.warning(f"Invalid date filter value: {value}. Error: {e}")
                    continue

            # AND logic across different fields:
            matching_ids = ans_qs.values_list('response_id', flat=True)
            qs = qs.filter(id__in=matching_ids)

        return qs.distinct()
