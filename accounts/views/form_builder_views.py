from tracemalloc import start
from forms_engine.models import DynamicForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from accounts.models import User, StudentProfile, TeacherProfile, Department, Section
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from forms_engine.models import DynamicForm, FormQuestion, QuestionOption, FormResponse, PublicFormResponse, PublicFormAnswer, FormAnswer
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_protect
from collections import Counter
from io import BytesIO
import qrcode
from django.core.files import File
from functools import wraps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import update_session_auth_hash


def edit_form(request, form_id):

    form = get_object_or_404(

        DynamicForm,

        id=form_id
    )

    questions = FormQuestion.objects.filter(

    form=form

    ).order_by(

        'order'
    )

    if request.method == 'POST':

        # ==========================================
        # FORM UPDATE
        # ==========================================

        form.title = request.POST.get(

            'title'
        )

        form.description = request.POST.get(

            'description'
        )

        form.start_date = request.POST.get(

            'start_date'
        )

        form.deadline_date = request.POST.get(

            'deadline_date'
        )

        form.is_active = (

            request.POST.get(

                'is_active'
            ) == 'on'
        )

        form.save()

        # ==========================================
        # QUESTIONS
        # ==========================================

        for question in questions:

            question.question = request.POST.get(

                f'question_{question.id}'
            )

            question.required = (

                request.POST.get(

                    f'required_{question.id}'
                ) == 'on'
            )

            question.save()

            # ==========================================
            # OPTIONS
            # ==========================================

            for option in question.question_options.all():
    
                option_value = request.POST.get(

                    f'option_{option.id}'
                )

                # ======================================
                # PREVENT NULL VALUES
                # ======================================

                if option_value:

                    option.option_text = option_value

                    option.save()

                    return redirect(

                        'private_forms'
                    )

    return render(

        request,

        'accounts/edit_form.html',

        {

            'form': form,

            'questions': questions,
        }
    )

def delete_form(request, form_id):

    form = get_object_or_404(

        DynamicForm,

        id=form_id
    )

    if request.method == 'POST':

        form.delete()

        return redirect(

            'private_forms'
        )

    return render(

        request,

        'accounts/delete_form.html',

        {

            'form': form
        }
    )

def add_question(request, form_id):

    form = get_object_or_404(
        DynamicForm,
        id=form_id
    )

    from forms_engine.field_registry import FIELD_REGISTRY

    # ==========================================
    # POST REQUEST
    # ==========================================

    if request.method == 'POST':

        field_type = request.POST.get(

            'field_type'
        )

        # ==========================================
        # CREATE QUESTION
        # ==========================================

        question = FormQuestion.objects.create(

            form=form,

            question=request.POST.get(

                'question'
            ),

            field_type=field_type,
            placeholder=request.POST.get('placeholder', ''),
            required=(

                request.POST.get(

                    'required'
                ) == 'on'
            ),

            order=FormQuestion.objects.filter(

                form=form

            ).count() + 1
        )

        # ==========================================
        # OPTIONS
        # ==========================================

        if FIELD_REGISTRY.get(field_type, {}).get('needs_options', False):
            options_list = request.POST.getlist('options')
            for option in options_list:
                if option.strip():
                    QuestionOption.objects.create(question=question, option_text=option.strip())

        # ==========================================
        # CONDITIONAL LOGIC
        # ==========================================
        from forms_engine.models import FormQuestionCondition, FormResponse, PublicFormResponse
        parent_question_id = request.POST.get('parent_question')
        if parent_question_id:
            try:
                parent_question = FormQuestion.objects.get(id=parent_question_id, form=form)
                if parent_question.id != question.id:
                    FormQuestionCondition.objects.create(
                        question=question,
                        parent_question=parent_question,
                        operator=request.POST.get('operator', 'equals'),
                        trigger_value=request.POST.get('trigger_value', ''),
                        action=request.POST.get('action', 'show')
                    )
            except FormQuestion.DoesNotExist:
                # Invalid parent question id or belongs to another form
                pass

        # ==========================================
        # VERSION BUMP
        # ==========================================
        form.version += 1
        form.save(update_fields=['version'])
        
        FormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')
        PublicFormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')

        # ==========================================
        # REDIRECT
        # ==========================================

        return redirect(
            'edit_form',
            form_id=form.id
        )

    # ==========================================
    # GET REQUEST
    # ==========================================
    
    existing_questions = FormQuestion.objects.filter(form=form).order_by('order')

    return render(

        request,

        'accounts/add_question.html',

        {
            'form': form,
            'field_registry': FIELD_REGISTRY,
            'existing_questions': existing_questions,
        }
    )

from django.http import JsonResponse

def get_form_questions(request, form_id):
    form = get_object_or_404(DynamicForm, id=form_id)
    questions = FormQuestion.objects.filter(form=form).order_by('order')
    
    data = []
    for q in questions:
        if not q.is_system_field:
            data.append({
                'id': q.id,
                'question': q.question,
                'field_type_display': q.get_field_type_display(),
            })
            
    return JsonResponse({'questions': data})

def delete_question(request, question_id):

    question = get_object_or_404(

        FormQuestion,

        id=question_id
    )

    form_id = question.form.id
    form = question.form

    question.delete()

    from forms_engine.models import FormResponse, PublicFormResponse
    form.version += 1
    form.save(update_fields=['version'])
    FormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')
    PublicFormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')

    return redirect('edit_form', form_id=form_id)

def delete_option(request, option_id):

    option = get_object_or_404(

        QuestionOption,

        id=option_id
    )

    form_id = option.question.form.id
    form = option.question.form

    option.delete()

    from forms_engine.models import FormResponse, PublicFormResponse
    form.version += 1
    form.save(update_fields=['version'])
    FormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')
    PublicFormResponse.objects.filter(form=form, form_version__lt=form.version).update(status='pending_update')

    return redirect('edit_form', form_id=form_id)

def preview_form(request, form_id):

    form = get_object_or_404(

        DynamicForm,

        id=form_id
    )

    questions = FormQuestion.objects.filter(

        form=form

    ).order_by(

        'order'
    )

    return render(

        request,

        'accounts/preview_form.html',

        {

            'form': form,

            'questions': questions,
        }
    )