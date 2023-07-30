from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .functions.calculate import get_coordinates_and_objects

def index(request):
    return render(request=request, template_name="RMapp/index.html")
    
def create_routes(request):
    if request.method == 'POST':
        Origen = request.POST['Origin_form']
        Destinos = request.POST.getlist('Destino_form')
        Origin_Object = get_coordinates_and_objects(Origen,Destinos)
        return render(request=request, template_name='RMapp/cr.html', context={
            'Origen'  : Origin_Object,
            'Destino' : Origin_Object.relational_nodos.all()
            })
    return HttpResponse('<p>FALLO FALTAL</p>')