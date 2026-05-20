from django.urls import path

from . import views

urlpatterns = [

    # ==========================================
    # IDENTIFIED
    # ==========================================

    path(
        'identified/summary/<int:form_id>/',
        views.identified_summary_excel,
        name='identified_summary_excel'
    ),

    path(
        'identified/detailed/<int:form_id>/',
        views.identified_detailed_pdf,
        name='identified_detailed_pdf'
    ),

    
    
    path(

    'public/excel/<int:form_id>/',

    views.public_form_excel,

    name='public_form_excel'
    
    
),
    path(

    'public/pdf/<int:form_id>/',

    views.public_detailed_pdf,

    name='public_detailed_pdf'
),
    path(

    'private-anonymous-pdf/<int:form_id>/',

    views.private_anonymous_pdf,

    name='private_anonymous_pdf'
),

path(

    'private-anonymous-excel/<int:form_id>/',

    views.private_anonymous_excel,

    name='private_anonymous_excel'
),
    
]