from django.urls import path

from . import views


urlpatterns = [

    path(

    'information-page/',

    views.information_page,

    name='information_page'
),

    # ==========================================
    # AUTHENTICATION
    # ==========================================

    path(

        'login/',

        views.user_login,

        name='login'
    ),

    path(

        'logout/',

        views.user_logout,

        name='logout'
    ),

    path(

        'password-change/',

        views.UserPasswordChangeView.as_view(),

        name='password_change'
    ),

    # ==========================================
    # DASHBOARDS
    # ==========================================

    path(

        'admin-dashboard/',

        views.admin_dashboard,

        name='admin_dashboard'
    ),

    path(

        'teacher-dashboard/',

        views.teacher_dashboard,

        name='teacher_dashboard'
    ),

    path(

        'student-dashboard/',

        views.student_dashboard,

        name='student_dashboard'
    ),

    # ==========================================
    # TEACHER MODULE
    # ==========================================

    path(

        'teacher-form-detail/<int:form_id>/',

        views.teacher_form_detail,

        name='teacher_form_detail'
    ),

    path(

        'student-response/<int:response_id>/',

        views.student_response_detail,

        name='student_response_detail'
    ),

   
    

    # ==========================================
    # ADMIN MODULE
    # ==========================================

    path(

        'manage-users/',

        views.manage_users,

        name='manage_users'
    ),

    path(

        'students-list/',

        views.students_list,

        name='students_list'
    ),

    path(

        'teachers-list/',

        views.teachers_list,

        name='teachers_list'
    ),

    # ==========================================
    # FORMS
    # ==========================================

    path(

        'private-forms/',

        views.private_forms,

        name='private_forms'
    ),

    path(

        'public-forms/',

        views.public_forms,

        name='public_forms'
    ),

    path(

        'teacher-forms/',

        views.teacher_forms,

        name='teacher_forms'
    ),

    # ==========================================
    # PUBLIC FORM SYSTEM
    # ==========================================
    # ==========================================
# PUBLIC FORMS
# ==========================================



path(
    'public-active-forms/',
    views.public_active_forms,
    name='public_active_forms'
),

path(
    'public-future-forms/',
    views.public_future_forms,
    name='public_future_forms'
),

path(
    'public-expired-forms/',
    views.public_expired_forms,
    name='public_expired_forms'
),

    path(

        'public-form-qr/<int:form_id>/',

        views.public_form_qr,

        name='public_form_qr'
    ),

    path(

        'public-form-users/<int:form_id>/',

        views.public_form_users,

        name='public_form_users'
    ),

    path(

        'public-form-detail/<int:form_id>/',

        views.public_form_detail,

        name='public_form_detail'
    ),
    
    
    path(

    'edit-form/<int:form_id>/',

    views.edit_form,

    name='edit_form'),

    path(

        'delete-form/<int:form_id>/',

        views.delete_form,

        name='delete_form'
    ),
    
        path(

        'add-question/<int:form_id>/',

        views.add_question,

        name='add_question'
    ),

    path(

        'delete-question/<int:question_id>/',

        views.delete_question,

        name='delete_question'
    ),
    path(

    'preview-form/<int:form_id>/',

    views.preview_form,

    name='preview_form'
),
    
    path(

    'delete-option/<int:option_id>/',

    views.delete_option,

    name='delete_option'),

path(
    'active-forms/',
    views.active_forms,
    name='active_forms'
),

path(
    'completed-forms/',
    views.completed_forms,
    name='completed_forms'
),

path(
    'upcoming-forms/',
    views.upcoming_forms,
    name='upcoming_forms'
),

path(
    'pending-forms/',
    views.pending_forms,
    name='pending_forms'
),

path(

    'public-forms-dashboard/',

    views.public_forms_dashboard,

    name='public_forms_dashboard'
),


path(

    'teacher-completed-forms/',

    views.teacher_completed_forms,

    name='teacher_completed_forms'
),


path(

    'teacher-active-forms/',

    views.teacher_active_forms,

    name='teacher_active_forms'
),

path(

    'teacher-upcoming-forms/',

    views.teacher_upcoming_forms,

    name='teacher_upcoming_forms'
),

# STUDENTS

path(
    'add-student/',
    views.add_student,
    name='add_student'
),

path(
    'edit-student/<int:student_id>/',
    views.edit_student,
    name='edit_student'
),

path(
    'delete-student/<int:student_id>/',
    views.delete_student,
    name='delete_student'
),
path(

    'teacher-students/',

    views.teacher_students,

    name='teacher_students'
),

path(
    'add-teacher/',
    views.add_teacher,
    name='add_teacher'
),

path(
    'edit-teacher/<int:teacher_id>/',
    views.edit_teacher,
    name='edit_teacher'
),

path(
    'delete-teacher/<int:teacher_id>/',
    views.delete_teacher,
    name='delete_teacher'
),
path(
    'teachers-list/',
    views.teachers_list,
    name='teachers_list'
),

path(

    'expired-forms/',

    views.expired_forms,

    name='expired_forms'
),


]