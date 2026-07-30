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

@admin.register(FormAnswer)
class FormAnswerAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'response',

        'question',

        'answer',
    )


# =========================================================
# PUBLIC FORM RESPONSE ADMIN
# =========================================================
