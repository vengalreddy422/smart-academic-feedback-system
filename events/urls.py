from django.urls import path

from . import views

urlpatterns = [

    path(
        '',
        views.events_home,
        name='events_home'
    ),
]