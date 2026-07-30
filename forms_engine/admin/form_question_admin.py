from django.contrib import admin
from .dynamic_form_admin import QuestionOptionInline, FormQuestionConditionInline

from forms_engine.models import (
    DynamicForm,
    FormQuestion,
    QuestionOption,
    FormResponse,
    FormAnswer,
    PublicFormResponse,
    PublicFormAnswer,
    FormQuestionCondition,
)

@admin.register(FormQuestion)
class FormQuestionAdmin(admin.ModelAdmin):

    list_display = (

        'question',

        'field_type',

        'required',

        'form',
    )

    ordering = ['-created_at']

    list_filter = (

        'field_type',

        'required',
    )

    search_fields = (

    'question',

    'form__title',
    )

    autocomplete_fields = (

        'form',
    )

    fields = (

        'form',

        'question',

        'field_type',

        'required',

        'placeholder',

        'order',
    )

    inlines = [
        QuestionOptionInline,
        FormQuestionConditionInline
    ]


# =========================================================
# FORM RESPONSE ADMIN
# =========================================================
