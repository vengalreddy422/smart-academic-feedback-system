from forms_engine.models import DynamicForm, FormResponse, PublicFormResponse
from accounts.models import TeacherProfile
from reports.filters import FormReportFilterEngine

# Note: The exports logic in reports.views can be shifted here, or we can just import them in views.
# But for better orchestration, let's keep get_allowed_forms here.

def get_allowed_forms_for_user(user):
    """
    Returns a queryset of DynamicForms the user is allowed to report on.
    Admin: All forms.
    Teacher: Forms where at least one assigned-section student has responded.
    """
    if user.role == 'admin':
        return DynamicForm.objects.all().order_by('-created_at')
        
    elif user.role == 'teacher':
        try:
            teacher_profile = TeacherProfile.objects.get(user=user)
            assigned_sections = teacher_profile.assigned_sections.all()
            # Forms with responses from these sections
            form_ids = FormResponse.objects.filter(
                student__section__in=assigned_sections
            ).values_list('form_id', flat=True).distinct()
            
            return DynamicForm.objects.filter(id__in=form_ids).order_by('-created_at')
        except TeacherProfile.DoesNotExist:
            return DynamicForm.objects.none()
            
    return DynamicForm.objects.none()


def get_filtered_report_data(form, user, filter_params):
    """
    Uses the FormReportFilterEngine to get the filtered queryset.
    """
    return FormReportFilterEngine.apply_filters(form, user, filter_params)
