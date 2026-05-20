from django.db import models

from accounts.models import (

    StudentProfile,

    Department
)

import uuid

import qrcode

from io import BytesIO

from django.core.files import File

from datetime import datetime

from django.utils import timezone

class DynamicForm(models.Model):
    
    FORM_TYPES = (

        ('feedback', 'Feedback'),

        ('registration', 'Registration'),

        ('survey', 'Survey'),

        ('event', 'Event'),

        ('exam', 'Exam'),
    )

    ACCESS_TYPES = (

        ('private', 'Private'),

        ('public', 'Public'),
    )
        # ==========================================
    # IDENTITY TYPES
    # ==========================================

    IDENTITY_TYPES = (

        ('identified', 'Identified'),

        ('anonymous', 'Anonymous'),
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    form_type = models.CharField(
        max_length=50,
        choices=FORM_TYPES
    )

    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPES,
        default='private'
    )
    identity_type = models.CharField(

    max_length=20,

    choices=IDENTITY_TYPES,

    default='anonymous')

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    qr_code = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True
    )

    # ==========================================
    # FORM START DATE & TIME
    # ==========================================

    start_date = models.DateField(
        null=True,
        blank=True
    )

    start_time = models.TimeField(
        null=True,
        blank=True
    )

    # ==========================================
    # FORM DEADLINE DATE & TIME
    # ==========================================

    deadline_date = models.DateField(
        null=True,
        blank=True
    )

    deadline_time = models.TimeField(
        null=True,
        blank=True
    )

   # ==========================================
    # ACTIVE STATUS
    # ==========================================

    is_active = models.BooleanField(
        default=True
    )

    # ==========================================
    # DEPARTMENT & SECTION ASSIGNMENT
    # ==========================================

   

   

    # ==========================================
    # CREATED & UPDATED
    # ==========================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )
         

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ==========================================
    # START DATETIME
    # ==========================================

    def get_start_datetime(self):

        if self.start_date and self.start_time:

            return datetime.combine(

                self.start_date,

                self.start_time

            )

        return None

    # ==========================================
    # DEADLINE DATETIME
    # ==========================================

    def get_deadline_datetime(self):

        if self.deadline_date and self.deadline_time:

            return datetime.combine(

                self.deadline_date,

                self.deadline_time

            )

        return None

    # ==========================================
    # FORM STARTED?
    # ==========================================

    def is_started(self):

        start_datetime = self.get_start_datetime()

        if start_datetime:

            current_datetime = timezone.localtime().replace(
                tzinfo=None
            )

            return current_datetime >= start_datetime

        return True

    # ==========================================
    # FORM EXPIRED?
    # ==========================================

    def is_expired(self):

        deadline_datetime = self.get_deadline_datetime()

        if deadline_datetime:

            current_datetime = timezone.localtime().replace(
                tzinfo=None
            )

            return current_datetime > deadline_datetime

        return False

    # ==========================================
    # STRING REPRESENTATION
    # ==========================================

    def __str__(self):

        return self.title

    # ==========================================
# QR CODE SAVE + AUTO SYSTEM FIELDS
# ==========================================

    def save(self, *args, **kwargs):
    
    # ==========================================
    # CHECK NEW FORM
    # ==========================================

        is_new = self.pk is None

        super().save(*args, **kwargs)

        # ==========================================
        # QR CODE GENERATION
        # ==========================================

        qr_data = (
            f"http://127.0.0.1:8000/forms/public-form/{self.uuid}/"
        )

        qr_image = qrcode.make(qr_data)

        buffer = BytesIO()

        qr_image.save(

            buffer,

            format='PNG'
        )

        file_name = f'{self.title}.png'

        self.qr_code.save(

            file_name,

            File(buffer),

            save=False
        )

        super().save(update_fields=['qr_code'])

        # ==========================================
        # AUTO CREATE SYSTEM FIELDS
        # ==========================================

        if (

            is_new

            and

            self.access_type == 'public'

            and

            self.identity_type == 'identified'
        ):

            system_fields = [

                ('Name', 'text'),

                ('Email', 'email'),

                ('College', 'text'),

                ('Branch', 'text'),
            ]

            # ==========================================
            # SYSTEM FIELD ORDER
            # ==========================================

            system_order = 1

            for question_text, field_type in system_fields:

                FormQuestion.objects.create(

                    form=self,

                    question=question_text,

                    field_type=field_type,

                    required=True,

                    order=system_order,

                    is_system_field=True
                )

                system_order += 1
class FormQuestion(models.Model):

    FIELD_TYPES = (

        ('text', 'Text Input'),

        ('textarea', 'Textarea'),

        ('radio', 'Radio Button'),

        ('checkbox', 'Checkbox'),

        ('select', 'Dropdown'),

        ('rating', 'Rating'),

        ('number', 'Number'),

        ('email', 'Email'),

        ('date', 'Date'),
    )

    form = models.ForeignKey(
        DynamicForm,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    question = models.CharField(
        max_length=500
    )

    field_type = models.CharField(
        max_length=50,
        choices=FIELD_TYPES,
        default='text'
    )

    placeholder = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


    required = models.BooleanField(
        default=True
    )

    order = models.IntegerField(
    default=0
)

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    is_system_field = models.BooleanField(
    default=False
    )
    
  

    class Meta:

        ordering = ['order']

    def __str__(self):

        return self.question

    def get_options(self):
    
        return self.question_options.all()


class FormResponse(models.Model):

    form = models.ForeignKey(
        DynamicForm,
        on_delete=models.CASCADE
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        unique_together = (
            'form',
            'student'
        )

    def __str__(self):

        return f"{self.student} - {self.form}"


class FormAnswer(models.Model):

    response = models.ForeignKey(
        FormResponse,
        on_delete=models.CASCADE
    )

    question = models.ForeignKey(
        FormQuestion,
        on_delete=models.CASCADE
    )

    answer = models.TextField()

    def __str__(self):

        return self.answer


class PublicFormResponse(models.Model):
    
    form = models.ForeignKey(
        DynamicForm,
        on_delete=models.CASCADE
    )

    # ==========================================
    # IDENTIFIED USER DETAILS
    # ==========================================

    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    college = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    branch = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # ==========================================
    # SUBMITTED TIME
    # ==========================================

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"Public Response - {self.form.title}"

class PublicFormAnswer(models.Model):

    response = models.ForeignKey(
        PublicFormResponse,
        on_delete=models.CASCADE
    )

    question = models.ForeignKey(
        FormQuestion,
        on_delete=models.CASCADE
    )

    answer = models.TextField()

    def __str__(self):

        return self.answer

class QuestionOption(models.Model):
    
    question = models.ForeignKey(

        FormQuestion,

        on_delete=models.CASCADE,

        related_name='question_options'
    )

    option_text = models.CharField(
        max_length=255
    )

    def __str__(self):

        return self.option_text