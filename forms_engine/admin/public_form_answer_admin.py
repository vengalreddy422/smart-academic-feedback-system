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

@admin.register(PublicFormAnswer)
class PublicFormAnswerAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'response',

        'question',

        'answer',
    )
