import pandas as pd

from django.db import close_old_connections
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect, render
from django.urls import path

from .models import (
    User,
    Department,
    Section,
    StudentProfile,
    TeacherProfile,
)


class ExcelUploadForm(forms.Form):

    excel_file = forms.FileField()


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    model = User

    fieldsets = UserAdmin.fieldsets + (

        (
            'Role Information',
            {
                'fields': (
                    'role',
                ),
            },
        ),

    )

    add_fieldsets = UserAdmin.add_fieldsets + (

        (
            'Role Information',
            {
                'fields': (
                    'role',
                ),
            },
        ),

    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

    list_display = (
        'name',
    )

    search_fields = (
        'name',
    )


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'department',
    )

    list_filter = (
        'department',
    )

    search_fields = (
        'name',
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'department',
        'roll_number',
        'semester',
        'section',
        'phone_number',
    )

    list_filter = (
        'department',
        'semester',
        'section',
    )

    search_fields = (
        'user__username',
        'roll_number',
        'phone_number',
    )

    change_list_template = (
    'admin/studentprofile_changelist.html'
)   
    def get_urls(self):

        urls = super().get_urls()

        custom_urls = [

            path(

                'upload-students/',

                self.admin_site.admin_view(

                    self.upload_students
                ),

                name='upload_students',
            ),

        ]

        return custom_urls + urls

    def upload_students(self, request):
    
        close_old_connections()

        if request.method == 'POST':

            try:

                form = ExcelUploadForm(

                    request.POST,

                    request.FILES
                )

                # ==========================================
                # FORM VALIDATION
                # ==========================================

                if form.is_valid():

                    excel_file = request.FILES[
                        'excel_file'
                    ]

                    # ==========================================
                    # READ EXCEL
                    # ==========================================

                    df = pd.read_excel(

                        excel_file,

                        engine='openpyxl'
                    )

                    # ==========================================
                    # REMOVE COLUMN SPACES
                    # ==========================================

                    df.columns = df.columns.str.strip()

                    print('Excel File Loaded Successfully')

                    # ==========================================
                    # LOOP ROWS
                    # ==========================================

                    for _, row in df.iterrows():

                        # ==========================================
                        # EXCEL VALUES
                        # ==========================================

                        roll_number = str(

                            row['roll_number']

                        ).strip()

                        student_name = str(

                            row['student_name']

                        ).strip()

                        department_name = str(

                            row['department']

                        ).strip()

                        semester = int(

                            row['semester']
                        )

                        section_name = str(

                            row['section']

                        ).strip()

                        # ==========================================
                        # DEPARTMENT
                        # ==========================================

                        department, _ = Department.objects.get_or_create(

                            name=department_name
                        )

                        # ==========================================
                        # SECTION
                        # ==========================================

                        section, _ = Section.objects.get_or_create(

                            department=department,

                            name=section_name,

                            semester=semester
                        )

                        # ==========================================
                        # SKIP EXISTING USERS
                        # ==========================================

                        if User.objects.filter(

                            username=roll_number

                        ).exists():

                            print(

                                f'{roll_number} already exists'
                            )

                            continue

                        # ==========================================
                        # CREATE USER
                        # ==========================================

                        user = User.objects.create_user(

                            username=roll_number,

                            password='Reset@2025',

                            first_name=student_name,

                            role='student',
                        )

                        # ==========================================
                        # CREATE STUDENT PROFILE
                        # ==========================================

                        StudentProfile.objects.create(

                            user=user,

                            department=department,

                            section=section,

                            roll_number=roll_number,

                            semester=semester,
                        )

                        print(

                            f'{roll_number} imported successfully'
                        )

                    # ==========================================
                    # SUCCESS MESSAGE
                    # ==========================================

                    self.message_user(

                        request,

                        'Students Imported Successfully',

                        messages.SUCCESS
                    )

                    return redirect('../')

                else:

                    print('Form Validation Failed')

                    print(form.errors)

            except Exception as e:

                print('Upload Error:', str(e))

                self.message_user(

                    request,

                    str(e),

                    messages.ERROR
                )

        # ==========================================
        # GET REQUEST
        # ==========================================

        form = ExcelUploadForm()

        context = {

            'form': form,

            'title': 'Upload Students Excel File',
        }

        return render(

            request,

            'admin/student_upload.html',

            context
        )
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'department',
        'phone_number',
    )

    list_filter = (
        'department',
    )

    search_fields = (
        'user__username',
        'phone_number',
    )