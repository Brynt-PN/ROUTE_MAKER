from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from functions.calculate import get_coordinates
def index(request):
    return render(request=request, template_name="RMapp/index.html")
    
def create_routes(request):
    if request.method == 'POST':
        Origen = request.POST['Origin_form']
        Destinos = request.POST.getlist('Destino_form')
        Dic_Adresses = {
            'Origen'  : Origen,
            'Destino' : Destinos
        }
        Origin_Object, Destinos_Objects = get_coordinates(Dic_Adresses)
        return render(request=request, template_name='RMapp/cr.html', context={
            'Origen'  : Origin_Object.raw,
            'Destino' : Destinos_Objects
            })
    return HttpResponse('<p>FALLO FALTAL</p>')