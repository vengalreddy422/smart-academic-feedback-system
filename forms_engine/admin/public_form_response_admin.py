from django.contrib import admin

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

@admin.register(PublicFormResponse)
class PublicFormResponseAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'form',

        'status',

        'form_version',

        'submitted_at',
    )


# =========================================================
# PUBLIC FORM ANSWER ADMIN
# =========================================================
