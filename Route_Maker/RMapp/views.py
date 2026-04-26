from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from .functions.calculate import get_coordinates_and_objects
from django.urls import reverse
from .models import Origin, Route, Nodo

@login_required
def index(request):
    return render(
        request=request,
        template_name="RMapp/index.html",
        context={
            'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
            'organization_name': request.user.organization.name if request.user.organization else '',
        },
    )
    
@login_required
def create_routes(request):
    if request.method == 'POST':
        Origen = request.POST['Origin_form']
        Destinos = request.POST.getlist('Destino_form')
        Origin_Object = get_coordinates_and_objects(Origen,Destinos, request.user.organization)
        Route_0 = Origin_Object.define_all_routes()
        return HttpResponseRedirect(redirect_to=reverse('RMapp:routes', args=(Route_0.id,)))
    return HttpResponse('<p>FALLO FALTAL</p>')

@login_required
def routes(request, id):
    Route_0 = get_object_or_404(
        Route.objects.select_related('origin'),
        pk=id,
        origin__organization=request.user.organization,
    )
    origin = Route_0.origin
    return render(request=request, template_name="RMapp/cr.html", context={
        'Origin' : origin,
        'Route'  : Route_0,
        'organization_name': request.user.organization.name if request.user.organization else '',
    })
