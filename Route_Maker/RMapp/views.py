from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .functions.calculate import get_coordinates_and_objects
from .models import Route, SavedPlace
from .providers.geoapify import GeoapifyError, get_geocoding_client


def _serialize_saved_place(place: SavedPlace) -> dict:
    return {
        "id": f"local-{place.id}",
        "formatted_address": place.address,
        "address_line1": place.label or place.address,
        "address_line2": "Guardado en tu negocio",
        "latitude": float(place.lat),
        "longitude": float(place.lon),
        "source": "local",
        "is_favorite": place.is_favorite,
        "usage_count": place.usage_count,
    }


def _get_local_place_suggestions(organization, query: str, limit: int = 5) -> list[dict]:
    if not organization:
        return []

    saved_places = organization.saved_places.filter(
        Q(address__icontains=query) | Q(label__icontains=query)
    )[:limit]
    return [_serialize_saved_place(place) for place in saved_places]


def _merge_autocomplete_results(local_results: list[dict], remote_results: list[dict], limit: int = 6) -> list[dict]:
    merged = []
    seen = set()

    for result in [*local_results, *remote_results]:
        normalized = result["formatted_address"].strip().lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        merged.append(result)
        if len(merged) >= limit:
            break

    return merged


def _remember_place(organization, address: str, lat, lon, place_kind: str) -> None:
    if not organization:
        return

    saved_place, created = SavedPlace.objects.get_or_create(
        organization=organization,
        address=address,
        place_kind=place_kind,
        defaults={
            "label": address.split(",")[0][:120],
            "lat": lat,
            "lon": lon,
            "usage_count": 1,
        },
    )

    if created:
        return

    saved_place.lat = lat
    saved_place.lon = lon
    if not saved_place.label:
        saved_place.label = address.split(",")[0][:120]
    saved_place.save(update_fields=["lat", "lon", "label", "last_used_at"])
    SavedPlace.objects.filter(pk=saved_place.pk).update(usage_count=F("usage_count") + 1)


def _update_organization_base(organization, origin) -> None:
    if not organization:
        return

    organization.base_location_name = origin.name
    organization.base_lat = origin.lat
    organization.base_lon = origin.lon
    organization.save(update_fields=["base_location_name", "base_lat", "base_lon"])


@login_required
def index(request):
    organization = request.user.organization
    favorite_places = []
    recent_places = []
    base_location_name = ""

    if organization:
        favorite_places = list(organization.saved_places.filter(is_favorite=True)[:4])
        recent_places = list(organization.saved_places.all()[:6])
        base_location_name = organization.base_location_name

    return render(
        request=request,
        template_name="RMapp/index.html",
        context={
            "organization_name": organization.name if organization else "",
            "base_location_name": base_location_name,
            "favorite_places": favorite_places,
            "recent_places": recent_places,
        },
    )


@login_required
def create_routes(request):
    if request.method == "POST":
        origen = request.POST["Origin_form"]
        destinos = [destino for destino in request.POST.getlist("Destino_form") if destino.strip()]
        if not origen.strip() or not destinos:
            messages.error(request, "Debes ingresar un origen y al menos un destino.")
            return HttpResponseRedirect(redirect_to=reverse("RMapp:index"))

        try:
            origin_object = get_coordinates_and_objects(origen, destinos, request.user.organization)
        except GeoapifyError as exc:
            messages.error(request, str(exc))
            return HttpResponseRedirect(redirect_to=reverse("RMapp:index"))

        _update_organization_base(request.user.organization, origin_object)
        _remember_place(
            request.user.organization,
            origin_object.name,
            origin_object.lat,
            origin_object.lon,
            SavedPlace.PlaceKinds.ORIGIN,
        )
        for nodo in origin_object.relational_nodos.all():
            _remember_place(
                request.user.organization,
                nodo.name,
                nodo.lat,
                nodo.lon,
                SavedPlace.PlaceKinds.DESTINATION,
            )

        route_0 = origin_object.define_all_routes()
        return HttpResponseRedirect(redirect_to=reverse("RMapp:routes", args=(route_0.id,)))

    return HttpResponse("<p>FALLO FALTAL</p>")


@login_required
def autocomplete(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})

    organization = request.user.organization
    local_results = _get_local_place_suggestions(organization, query)
    proximity = None
    country_bias = ""

    if organization:
        country_bias = organization.country_code
        if organization.base_lat is not None and organization.base_lon is not None:
            proximity = (float(organization.base_lon), float(organization.base_lat))

    try:
        remote_results = get_geocoding_client().autocomplete(
            query,
            country_bias=country_bias,
            proximity=proximity,
        )
    except GeoapifyError as exc:
        if local_results:
            return JsonResponse({"results": local_results, "warning": str(exc)})
        return JsonResponse({"results": [], "error": str(exc)}, status=502)

    results = _merge_autocomplete_results(local_results, remote_results)
    return JsonResponse({"results": results})


@login_required
def routes(request, id):
    route_0 = get_object_or_404(
        Route.objects.select_related("origin"),
        pk=id,
        origin__organization=request.user.organization,
    )
    origin = route_0.origin
    route_data = route_0.json_dic()
    destinations = route_data["Destinos"][0]

    return render(
        request=request,
        template_name="RMapp/cr.html",
        context={
            "Origin": origin,
            "Route": route_0,
            "organization_name": request.user.organization.name if request.user.organization else "",
            "route_destinations": destinations,
            "route_stop_count": len(destinations),
        },
    )
