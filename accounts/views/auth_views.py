from tracemalloc import start

from forms_engine.models import DynamicForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpResponse
from django.db.models import Q

from accounts.models import (
    User,
    StudentProfile,
    TeacherProfile,
    Department,
    Section
)

from django.contrib.auth.decorators import login_required

from django.utils import timezone
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib import messages

from forms_engine.models import (
    PublicFormResponse,
)


from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
import openpyxl
from forms_engine.models import DynamicForm, FormResponse
from reportlab.lib import colors

from collections import Counter
from reportlab.lib.pagesizes import letter

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from collections import Counter
from accounts.models import User

from forms_engine.models import (

    DynamicForm,

    FormQuestion,

    QuestionOption,

    FormResponse,

    PublicFormResponse,

    PublicFormAnswer
)



from reportlab.lib.styles import getSampleStyleSheet

from io import BytesIO

import qrcode
from accounts.models import StudentProfile

from accounts.models import TeacherProfile

from accounts.models import (
    StudentProfile,
)

from forms_engine.models import (
    FormResponse,
    FormAnswer,
)

from functools import wraps
from django.shortcuts import redirect



from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponse

from django.shortcuts import render
from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponse

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

@csrf_protect
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
