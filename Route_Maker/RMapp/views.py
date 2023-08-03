from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .functions.calculate import get_coordinates_and_objects
from django.urls import reverse
from .models import Origin, Route, Nodo

def index(request):
    return render(request=request, template_name="RMapp/index.html")
    
def create_routes(request):
    if request.method == 'POST':
        Origen = request.POST['Origin_form']
        Destinos = request.POST.getlist('Destino_form')
        Origin_Object = get_coordinates_and_objects(Origen,Destinos)
        Route_0 = Origin_Object.define_all_routes()
        return HttpResponseRedirect(redirect_to=reverse('RMapp:routes', args=(Route_0.id,)))
    return HttpResponse('<p>FALLO FALTAL</p>')

def routes(request, id):
    Route_0 = get_object_or_404(Route, pk=id)
    origin = get_object_or_404(Origin, pk=Route_0.origin_id)
    return render(request=request, template_name="RMapp/cr.html", context={
        'Origin' : origin,
        'Route'  : Route_0
    })