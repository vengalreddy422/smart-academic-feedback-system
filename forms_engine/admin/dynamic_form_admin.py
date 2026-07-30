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

@admin.register(DynamicForm)
class DynamicFormAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'title',

        'form_type',

        'access_type',
        
        'identity_type',
       

      


        'is_active',

        # START & DEADLINE

        'start_date',

        'deadline_date',

        'uuid',

        'version',

        'created_at',
    )

    list_filter = (

        'form_type',

        'access_type',

        'identity_type',
        
        'is_active',
        
    )

    search_fields = (

    'title',
    )

    ordering = (

        '-id',
    )
    filter_horizontal = (

   

    
)

    readonly_fields = (

        'uuid',

        'qr_code',

        'version',

        'created_at',
    )

    fieldsets = (

        (

            'Form Information',

            {

                'fields': (

                'title',

                'description',

                'form_type',

                'access_type',

                'identity_type',
                
                'is_active',
                

             

                    # ==================================
                    # START DATE & TIME
                    # ==================================

                    'start_date',

                    'start_time',

                    # ==================================
                    # DEADLINE DATE & TIME
                    # ==================================

                    'deadline_date',

                    'deadline_time',
                )

            }

        ),

        (

            'Public Form Access',

            {

                'fields': (

                    'uuid',

                    'qr_code',
                )

            }

        ),

        (

            'Date Information',

            {

                'fields': (

                    'created_at',
                )

            }

        ),

    )
    
    

# =========================================================
# QUESTION OPTION INLINE
# =========================================================

class QuestionOptionInline(admin.TabularInline):

    model = QuestionOption

    extra = 1

from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

class FormQuestionConditionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.is_valid():
                continue
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                parent_question = form.cleaned_data.get('parent_question')
                if parent_question and self.instance and hasattr(self.instance, 'form'):
                    if parent_question.form != self.instance.form:
                        raise ValidationError("Parent question must belong to the same form.")
                    if self.instance.id and parent_question.id == self.instance.id:
                        raise ValidationError("Parent question cannot be the question itself.")

class FormQuestionConditionInline(admin.TabularInline):
    model = FormQuestionCondition
    fk_name = 'question'
    extra = 1
    formset = FormQuestionConditionFormSet

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent_question":
            from forms_engine.models import FormQuestion
            question_id = request.resolver_match.kwargs.get('object_id')
            if question_id:
                try:
                    question = FormQuestion.objects.get(id=question_id)
                    kwargs["queryset"] = FormQuestion.objects.filter(form=question.form).exclude(id=question.id).order_by('-created_at')
                except FormQuestion.DoesNotExist:
                    kwargs["queryset"] = FormQuestion.objects.all().order_by('-created_at')
            else:
                kwargs["queryset"] = FormQuestion.objects.all().order_by('-created_at')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# =========================================================
# FORM QUESTION ADMIN
# =========================================================
