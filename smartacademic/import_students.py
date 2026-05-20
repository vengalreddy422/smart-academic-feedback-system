import os

import django
import pandas as pd


os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'SMART_ACADEMIC_SYSTEM.settings'
)

django.setup()


from django.contrib.auth.hashers import make_password

from accounts.models import (
    User,
    StudentProfile,
    Department,
    Section,
)


df = pd.read_excel(
    'students.xlsx'
)


for _, row in df.iterrows():

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

    department, _ = Department.objects.get_or_create(
        name=department_name
    )

    section, _ = Section.objects.get_or_create(

        department=department,

        semester=semester,

        name=section_name,
    )

    if User.objects.filter(
        username=roll_number
    ).exists():

        print(
            f'{roll_number} already exists'
        )

        continue

    user = User.objects.create(

        username=roll_number,

        first_name=student_name,

        role='student',
    )

    user.set_password(
        'Reset@2025'
    )

    user.save()

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


print(
    'All students imported successfully'
)