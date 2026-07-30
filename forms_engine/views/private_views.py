from email import errors
from urllib import request

from django.contrib.auth.decorators import login_required

from django.http import HttpResponse

from django.shortcuts import (
    get_object_or_404,
    render,
)
from django.core.validators import validate_email

from django.core.exceptions import ValidationError

from accounts.models import StudentProfile

from forms_engine.models import (
    DynamicForm,
    FormAnswer,
    FormQuestion,
    FormResponse,
    PublicFormAnswer,
    PublicFormResponse,
)
from forms_engine.field_registry import validate_field

@login_required
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

@login_required
def submit_form(request, form_id):

    if getattr(request.user, "role", None) != "student":

        return HttpResponse(
            "Forbidden",
            status=403
        )

    if request.method != "POST":

        return HttpResponse(
            "Invalid Request Method",
            status=405
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

    questions = FormQuestion.objects.filter(form=form).order_by('-is_system_field', 'order', 'id')

    errors = {}
    answers_data = []

    # 1. Pre-fetch all submitted answers for condition evaluation
    submitted_answers = {}
    for question in questions:
        if question.field_type == "checkbox":
            submitted_answers[question.id] = ",".join(request.POST.getlist(str(question.id)))
        else:
            submitted_answers[question.id] = request.POST.get(str(question.id), "").strip()

    # 2. Evaluate conditions
    from forms_engine.models import FormQuestionCondition
    conditions = FormQuestionCondition.objects.filter(question__form=form)
    
    def is_question_active(q_id):
        q_conds = [c for c in conditions if c.question_id == q_id]
        if not q_conds:
            return True
        for c in q_conds:
            parent_val = submitted_answers.get(c.parent_question_id, "")
            if c.operator == 'equals' and parent_val != c.trigger_value: return False
            if c.operator == 'not_equals' and parent_val == c.trigger_value: return False
            if c.operator == 'contains' and c.trigger_value not in parent_val: return False
            try:
                if c.operator == 'greater_than' and float(parent_val) <= float(c.trigger_value): return False
                if c.operator == 'less_than' and float(parent_val) >= float(c.trigger_value): return False
            except ValueError:
                if c.operator in ['greater_than', 'less_than']: return False
        return True

    for question in questions:
        answer = submitted_answers[question.id]

        if not is_question_active(question.id):
            answer = "" # Clear answer if hidden
        else:
            # REQUIRED VALIDATION
            if question.required and not answer:
                errors[question.id] = f"{question.question} is required."
                continue

            # FORMAT VALIDATION
            if answer:
                is_valid, err_msg = validate_field(question.field_type, answer)
                if not is_valid:
                    errors[question.id] = err_msg
                    continue

        # STORE TEMP ANSWERS
        answers_data.append({
            "question": question,
            "answer": answer
        })

    # ==========================================
    # IF ERRORS
    # ==========================================

    if errors:
        _attach_options_list(questions)
        for q in questions:
            if q.id in errors:
                q.error = errors[q.id]
                
        conditions_data = []
        for cond in conditions:
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
                "errors": errors,
                "conditions_json": conditions_json,
                "is_pending_update": is_pending_update,
                "form_data": request.POST,
            },
        )

    # ==========================================
    # CREATE OR UPDATE RESPONSE
    # ==========================================

    if response_obj:
        response_obj.status = 'submitted'
        response_obj.form_version = form.version
        response_obj.save(update_fields=['status', 'form_version'])
        FormAnswer.objects.filter(response=response_obj).delete()
        response = response_obj
    else:
        response = FormResponse.objects.create(
            form=form,
            student=student_profile,
            status='submitted',
            form_version=form.version
        )

    # ==========================================
    # SAVE ANSWERS
    # ==========================================

    for item in answers_data:

        FormAnswer.objects.create(

            response=response,

            question=item["question"],

            answer=item["answer"],
        )

    return render(

        request,

        'forms_engine/form_success.html',

        {

            'username': request.user.first_name,

            'form_type': 'private',
        }
    )
    
def public_form(request, uuid):
    form = get_object_or_404(
        DynamicForm,
        uuid=uuid,
        is_active=True,
    )

    # Clean, simple ordering: First created stays first, newest goes to the bottom
    questions = FormQuestion.objects.filter(
        form=form
    ).order_by(
        'order', 
        'id'
    )   

    _attach_options_list(questions)

    if request.method == "POST":
        errors = {}
        answers_data = []

        for question in questions:
            if question.field_type == "checkbox":
                selected = request.POST.getlist(str(question.id))
                answer = ",".join(selected)
            else:
                answer = request.POST.get(str(question.id), "").strip()

            if question.required and not answer:
                errors[question.id] = f"{question.question} is required."
                continue

            is_valid, err_msg = validate_field(question.field_type, answer)
            if not is_valid:
                errors[question.id] = err_msg
                continue

            answers_data.append({
                "question": question,
                "answer": answer
            })

        if errors:
            for q in questions:
                if q.id in errors:
                    q.error = errors[q.id]

            return render(
                request,
                "forms_engine/public_form.html",
                {
                    "form": form,
                    "questions": questions,
                    "errors": errors,
                },
            )

        response = PublicFormResponse.objects.create(form=form)
        
        for item in answers_data:
            PublicFormAnswer.objects.create(
                response=response,
                question=item["question"],
                answer=item["answer"],
            )

        return render(
            request,
            'forms_engine/form_success.html',
            {
                'form_type': 'public',
            }
        )

    return render(
        request,
        "forms_engine/public_form.html",
        {
            "form": form,
            "questions": questions,
        },
    )
