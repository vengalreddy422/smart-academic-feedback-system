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

from .models import (
    DynamicForm,
    FormAnswer,
    FormQuestion,
    FormResponse,
    PublicFormAnswer,
    PublicFormResponse,
)
from .field_registry import validate_field


def _attach_options_list(questions):
    
    for question in questions:

        question.options_list = (
            question.question_options.all().order_by(
                'id'
            )
        )

    return questions


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

    already_submitted = FormResponse.objects.filter(

        form=form,

        student=student_profile,

    ).exists()

    if already_submitted:

        return HttpResponse(
            "You already submitted this form."
        )

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

    return render(

        request,

        "forms_engine/open_form.html",

        {

            "form": form,

            "questions": questions,
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
    already_submitted = FormResponse.objects.filter(

        form=form,

        student=student_profile,

    ).exists()

    if already_submitted:

        return HttpResponse(
            "You already submitted this form."
        )

    questions = FormQuestion.objects.filter(

    form=form

).order_by(

    '-is_system_field',

    'order',

    'id'
)

    errors = {}

    answers_data = []

    for question in questions:

        # ======================================
        # CHECKBOX
        # ======================================

        if question.field_type == "checkbox":

            selected = request.POST.getlist(
                str(question.id)
            )

            answer = ",".join(selected)

        else:

            answer = request.POST.get(
                str(question.id),
                ""
            ).strip()

        # ======================================
        # REQUIRED VALIDATION
        # ======================================

        if question.required and not answer:

            errors[question.id] = (

                f"{question.question} is required."
            )

            continue

        # ======================================
        # FORMAT VALIDATION
        # ======================================

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

        _attach_options_list(
            questions
        )

        for q in questions:
            if q.id in errors:
                q.error = errors[q.id]

        return render(

            request,

            "forms_engine/open_form.html",

            {

                "form": form,

                "questions": questions,

                "errors": errors,
            },
        )

    # ==========================================
    # CREATE RESPONSE
    # ==========================================

    response = FormResponse.objects.create(

        form=form,

        student=student_profile,
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