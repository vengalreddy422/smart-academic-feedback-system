from django.contrib import admin

from .models import (
    DynamicForm,
    FormQuestion,
    QuestionOption,
    FormResponse,
    FormAnswer,
    PublicFormResponse,
    PublicFormAnswer,
)


# =========================================================
# DYNAMIC FORM ADMIN
# =========================================================

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


# =========================================================
# FORM QUESTION ADMIN
# =========================================================

@admin.register(FormQuestion)
class FormQuestionAdmin(admin.ModelAdmin):

    list_display = (

        'question',

        'field_type',

        'required',

        'form',
    )

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
        QuestionOptionInline
    ]


# =========================================================
# FORM RESPONSE ADMIN
# =========================================================

@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'form',

        'student',

        'submitted_at',
    )

    search_fields = (

        'student__user__username',
    )


# =========================================================
# FORM ANSWER ADMIN
# =========================================================

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

@admin.register(PublicFormResponse)
class PublicFormResponseAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'form',

        'submitted_at',
    )


# =========================================================
# PUBLIC FORM ANSWER ADMIN
# =========================================================

@admin.register(PublicFormAnswer)
class PublicFormAnswerAdmin(admin.ModelAdmin):

    list_display = (

        'id',

        'response',

        'question',

        'answer',
    )