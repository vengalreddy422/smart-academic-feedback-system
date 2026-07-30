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

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            user_role = getattr(request.user, 'role', None)
            if user_role not in roles:
                return HttpResponse('Unauthorized', status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def information_page(request):
    
    return render(

        request,

        'accounts/information_page.html'
    )

def user_login(request):

    # ==========================
    # ALREADY LOGGED IN
    # ==========================

    if request.user.is_authenticated:

        if request.user.role == 'admin':

            return redirect(
                reverse('admin_dashboard')
            )

        if request.user.role == 'teacher':

            return redirect(
                reverse('teacher_dashboard')
            )

        if request.user.role == 'student':

            return redirect(
                reverse('student_dashboard')
            )

    # ==========================
    # LOGIN POST
    # ==========================

    if request.method == 'POST':

        username = request.POST.get(
            'username'
        )
        if username:
            username = username

        password = request.POST.get(
            'password'
        )

        user = authenticate(

            request,

            username=username,

            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            # ==========================
            # SESSION PERSISTENCE
            # ==========================

            request.session.set_expiry(
                86400
            )

            if user.role == 'admin':

                return redirect(
                    reverse('admin_dashboard')
                )

            if user.role == 'teacher':

                return redirect(
                    reverse('teacher_dashboard')
                )

            if user.role == 'student':

                return redirect(
                    reverse('student_dashboard')
                )

            return HttpResponse(

                'Role Not Found',

                status=403
            )

        return render(

            request,

            'accounts/login.html',

            {

                'error':
                'Invalid Username or Password'

            },

        )

    return render(

        request,

        'accounts/login.html'
    )

def user_logout(request):

    logout(request)

    return redirect(
        reverse('login')
    )


from django.contrib.auth.views import PasswordChangeView

from django.contrib.auth import update_session_auth_hash

from django.urls import reverse_lazy


from django.contrib.auth.views import PasswordChangeView

from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth import update_session_auth_hash

from django.urls import reverse_lazy

class UserPasswordChangeView(

    LoginRequiredMixin,

    PasswordChangeView

):

    template_name = 'accounts/password_change.html'

    success_url = reverse_lazy('student_dashboard')

    def form_valid(self, form):

        response = super().form_valid(form)

        # KEEP USER LOGGED IN

        update_session_auth_hash(

            self.request,

            form.user

        )

        return response
