from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .functions.calculate import get_coordinates_and_objects
from .providers.geoapify import GeoapifyError, get_geocoding_client
from django.urls import reverse
from .models import Route

@login_required
def index(request):
    return render(
        request=request,
        template_name="RMapp/index.html",
        context={
            'organization_name': request.user.organization.name if request.user.organization else '',
        },
    )
    
@login_required
def create_routes(request):
    if request.method == 'POST':
        Origen = request.POST['Origin_form']
        Destinos = [destino for destino in request.POST.getlist('Destino_form') if destino.strip()]
        if not Origen.strip() or not Destinos:
            messages.error(request, 'Debes ingresar un origen y al menos un destino.')
            return HttpResponseRedirect(redirect_to=reverse('RMapp:index'))

        try:
            Origin_Object = get_coordinates_and_objects(Origen,Destinos, request.user.organization)
        except GeoapifyError as exc:
            messages.error(request, str(exc))
            return HttpResponseRedirect(redirect_to=reverse('RMapp:index'))

        Route_0 = Origin_Object.define_all_routes()
        return HttpResponseRedirect(redirect_to=reverse('RMapp:routes', args=(Route_0.id,)))
    return HttpResponse('<p>FALLO FALTAL</p>')


@login_required
def autocomplete(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    try:
        results = get_geocoding_client().autocomplete(query)
    except GeoapifyError as exc:
        return JsonResponse({'results': [], 'error': str(exc)}, status=502)

    return JsonResponse({'results': results})

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
