import pandas as pd

from django.db import close_old_connections
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect, render
from django.urls import path

from accounts.models import (
    User,
    Department,
    Section,
    StudentProfile,
    TeacherProfile,
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
