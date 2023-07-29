from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

def index(request):
    return render(request=request, template_name="RMapp/index.html")
    
def create_routes(request):
    if request.method == 'POST':
        Origen = request.POST['Origin_form']
        Destinos = request.POST.getlist('Destino_form')
        return render(request=request, template_name='RMapp/cr.html', context={
            'Origen'  : Origen,
            'Destino' : Destinos
            })
    return HttpResponse('<p>FALLO FALTAL</p>')