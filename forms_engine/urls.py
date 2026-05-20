from django.urls import path

from . import views


urlpatterns = [



    path(
        'open-form/<int:form_id>/',
        views.open_form,
        name='open_form'
    ),

    path(
        'submit-form/<int:form_id>/',
        views.submit_form,
        name='submit_form'
    ),
    
    path(
    'public-form/<uuid:uuid>/',
    views.public_form,
    name='public_form'
),

]