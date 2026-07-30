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

@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'form',

        'student',

        'status',

        'form_version',

        'submitted_at',
    )

    search_fields = (

        'student__user__username',
    )


# =========================================================
# FORM ANSWER ADMIN
# =========================================================
