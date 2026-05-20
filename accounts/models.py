from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    def __str__(self):

        return self.username


class Department(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):

        return self.name


class Section(models.Model):

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )

    name = models.CharField(
        max_length=50
    )

    semester = models.IntegerField()

    class Meta:

        unique_together = (
            'department',
            'name',
            'semester',
        )

    def __str__(self):

        return (
            f"{self.department.name} "
            f"- Sem {self.semester} "
            f"- {self.name}"
        )


class StudentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE
    )

    roll_number = models.CharField(
        max_length=50,
        unique=True
    )

    semester = models.IntegerField()

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default=''
    )

    def __str__(self):

        return (
            f"{self.user.username} "
            f"({self.roll_number})"
        )


class TeacherProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )

    assigned_sections = models.ManyToManyField(
        Section,
        blank=True
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default=''
    )

    def __str__(self):

        return self.user.username