
from django.contrib import admin
from django.urls import path,include
from django.views.generic import RedirectView

from accounts import views

urlpatterns = [
    
      path(

        '',

        views.information_page,

        name='home'
    ),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('forms/', include('forms_engine.urls')),
    path('reports/', include('reports.urls')),
    path(
    'events/',
    include('events.urls')
),


    
]
