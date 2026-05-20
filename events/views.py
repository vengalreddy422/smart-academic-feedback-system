from django.http import HttpResponse

def events_home(request):

    return HttpResponse(
        'Events App Working'
    )