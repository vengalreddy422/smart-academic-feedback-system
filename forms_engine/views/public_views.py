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

def _attach_options_list(questions):
    
    for question in questions:

        question.options_list = (
            question.question_options.all().order_by(
                'id'
            )
        )

    return questions
