from email import errors
from urllib import request
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from accounts.models import StudentProfile
from forms_engine.models import DynamicForm, FormAnswer, FormQuestion, FormResponse, PublicFormAnswer, PublicFormResponse
from forms_engine.field_registry import validate_field

def _attach_options_list(questions):
    for question in questions:
        question.options_list = question.question_options.all().order_by('id')
    return questions


def open_form(request, form_id):

    if getattr(request.user, "role", None) != "student":

        return HttpResponse(
            "Forbidden",
            status=403
        )

    

    student_profile = get_object_or_404(

        StudentProfile,

        user=request.user
    )
    
    form = get_object_or_404(

    DynamicForm,

    id=form_id,

    is_active=True
)

    response_obj = FormResponse.objects.filter(
        form=form,
        student=student_profile
    ).first()

    already_submitted = response_obj is not None
    is_pending_update = already_submitted and response_obj.status == 'pending_update'

    if already_submitted and not is_pending_update:
        return HttpResponse("You already submitted this form.")

    # Retrieve existing answers if pending update
    existing_answers = {}
    answered_question_ids = []
    if is_pending_update:
        from forms_engine.models import FormAnswer
        answers = FormAnswer.objects.filter(response=response_obj)
        for ans in answers:
            existing_answers[str(ans.question_id)] = ans.answer
            answered_question_ids.append(ans.question_id)

    questions = FormQuestion.objects.filter(
    form=form
    ).extra(
    select={
        'system_first': """
        CASE
            WHEN is_system_field = TRUE THEN 0
            ELSE 1
        END
        """
    }
    ).order_by(
    'system_first',
    'id'   # first created comes first
    )

    _attach_options_list(
        questions
    )

    # Fetch conditions for JS
    from forms_engine.models import FormQuestionCondition
    conditions_qs = FormQuestionCondition.objects.filter(question__form=form)
    conditions_data = []
    for cond in conditions_qs:
        conditions_data.append({
            'question_id': cond.question_id,
            'parent_question_id': cond.parent_question_id,
            'operator': cond.operator,
            'trigger_value': cond.trigger_value,
            'action': cond.action
        })
    import json
    conditions_json = json.dumps(conditions_data)

    return render(
        request,
        "forms_engine/open_form.html",
        {
            "form": form,
            "questions": questions,
            "existing_answers": existing_answers,
            "conditions_json": conditions_json,
            "is_pending_update": is_pending_update,
            "form_data": existing_answers,
            "answered_question_ids": answered_question_ids,
        },
    )
