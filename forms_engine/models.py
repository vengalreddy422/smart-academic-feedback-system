from django.db import models
from accounts.models import StudentProfile, Department
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

    IDENTITY_TYPES = (
        ('identified', 'Identified'),
        ('anonymous', 'Anonymous'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    form_type = models.CharField(max_length=50, choices=FORM_TYPES)
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES, default='private')
    identity_type = models.CharField(max_length=20, choices=IDENTITY_TYPES, default='anonymous')
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    # ==========================================
    # FORM START DATE & TIME
    # ==========================================
    start_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)

    # ==========================================
    # FORM DEADLINE DATE & TIME
    # ==========================================
    deadline_date = models.DateField(null=True, blank=True)
    deadline_time = models.TimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_start_datetime(self):
        if self.start_date and self.start_time:
            return datetime.combine(self.start_date, self.start_time)
        return None

    def get_deadline_datetime(self):
        if self.deadline_date and self.deadline_time:
            return datetime.combine(self.deadline_date, self.deadline_time)
        return None

    def is_started(self):
        start_datetime = self.get_start_datetime()
        if start_datetime:
            current_datetime = timezone.localtime().replace(tzinfo=None)
            return current_datetime >= start_datetime
        return True

    def is_expired(self):
        deadline_datetime = self.get_deadline_datetime()
        if deadline_datetime:
            current_datetime = timezone.localtime().replace(tzinfo=None)
            return current_datetime > deadline_datetime
        return False

    def __str__(self):
        return self.title

    # =====================================================================
    # REFINED SAVE METHOD (NO AUTOMATIC SYSTEM FIELDS GENERATED HERE)
    # =====================================================================
    def save(self, *args, **kwargs):
        
        # 1. Guard against infinite loop during single-field updates
        if kwargs.get('update_fields') and 'qr_code' in kwargs['update_fields']:
            super().save(*args, **kwargs)
            return

        # 2. Save parent record metadata properties 
        super().save(*args, **kwargs)

        # 3. Generate QR code mapping payload dynamically
        qr_data = f"https://feedback-system-s3ty.onrender.com/forms/public-form/{self.uuid}/"

        print("QR URL =", qr_data)        
        qr_image = qrcode.make(qr_data)

        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        file_name = f'{self.title}_{self.uuid}.png'

        self.qr_code.save(file_name, File(buffer), save=False)
        
        # 4. Finalize file write transaction strictly isolated to the image update column
        super().save(update_fields=['qr_code'])


class FormQuestion(models.Model):

    from .field_registry import get_field_choices
    FIELD_TYPES = get_field_choices()

    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name='questions')
    question = models.CharField(max_length=500)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES, default='text')
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_system_field = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question

    def get_options(self):
        return self.question_options.all()


class FormResponse(models.Model):
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('form', 'student')

    def __str__(self):
        return f"{self.student} - {self.form}"


class FormAnswer(models.Model):
    response = models.ForeignKey(FormResponse, on_delete=models.CASCADE)
    question = models.ForeignKey(FormQuestion, on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)
    uploaded_file = models.FileField(upload_to='resumes/', blank=True, null=True)

    def __str__(self):
        return self.answer if self.answer else ""


class PublicFormResponse(models.Model):
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Public Response - {self.form.title}"
    
    
class PublicFormAnswer(models.Model):
    response = models.ForeignKey(PublicFormResponse, on_delete=models.CASCADE)
    question = models.ForeignKey(FormQuestion, on_delete=models.CASCADE)
    answer = models.TextField()

    def __str__(self):
        return self.answer


class QuestionOption(models.Model):
    question = models.ForeignKey(FormQuestion, on_delete=models.CASCADE, related_name='question_options')
    option_text = models.CharField(max_length=255)

    def __str__(self):
        return self.option_text