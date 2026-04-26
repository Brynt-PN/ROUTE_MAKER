from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from urllib.parse import quote
import simplejson as json

from .functions.calculate import get_coordinates_and_objects
from .models import DispatchStop, Route, SavedPlace
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
        "country_code": place.organization.country_code,
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


def _build_recent_batch_entries(organization, limit: int = 4) -> list[dict]:
    if not organization:
        return []

    entries = []
    for batch in organization.dispatch_batches.all()[:limit]:
        first_origin = batch.origins.order_by("id").first()
        first_route = first_origin.relational_route.order_by("sequence_number", "id").first() if first_origin else None
        entries.append(
            {
                "name": batch.name,
                "total_stops": batch.total_stops,
                "status": batch.get_status_display(),
                "first_route_id": first_route.id if first_route else None,
            }
        )
    return entries


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


def _build_route_entries(origin, current_route_id: int) -> tuple[list[dict], int]:
    routes = list(origin.relational_route.order_by("sequence_number", "id"))
    entries = []
    current_display_number = 1

    for route in routes:
        route_data = route.json_dic()
        stop_count = len(route_data["Destinos"][0])
        entry = {
            "id": route.id,
            "display_number": route.sequence_number,
            "stop_count": stop_count,
            "is_current": route.id == current_route_id,
        }
        if route.id == current_route_id:
            current_display_number = route.sequence_number
        entries.append(entry)

    return entries, current_display_number


def _build_share_text(display_number: int, origin_name: str, destinations: list[str]) -> str:
    lines = [
        f"Ruta {display_number}",
        f"Origen: {origin_name}",
        "Paradas:",
    ]
    lines.extend(f"{index}. {address}" for index, address in enumerate(destinations, start=1))
    return "\n".join(lines)


def _build_whatsapp_share_text(
    display_number: int,
    origin_name: str,
    destinations: list[str],
    google_maps_directions_url: str,
) -> str:
    base_text = _build_share_text(display_number, origin_name, destinations)
    if google_maps_directions_url:
        return f"{base_text}\n\nMapa: {google_maps_directions_url}"
    return f"{base_text}\n\nAbre cada parada desde Route Maker para navegar tramo por tramo."


def _build_google_maps_directions_url(origin_name: str, destinations: list[str]) -> str:
    if not destinations:
        return ""

    destination = destinations[-1]
    waypoints = destinations[:-1]
    url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={quote(origin_name)}"
        f"&destination={quote(destination)}"
    )
    if waypoints:
        url += "&waypoints=" + quote("|".join(waypoints))
    return url


def _build_route_payload(origin_name: str, destinations: list[str]) -> str:
    return json.dumps(
        {
            "Origin": origin_name,
            "Destinos": [destinations],
        },
        ensure_ascii=False,
    )


def _build_step_navigation_links(origin_name: str, destinations: list[dict]) -> list[dict]:
    previous_address = origin_name
    step_links = []

    for index, destination in enumerate(destinations, start=1):
        address = destination["address"]
        step_links.append(
            {
                "index": index,
                "address": address,
                "stop_id": destination.get("stop_id"),
                "can_move_previous": destination.get("can_move_previous", False),
                "can_move_next": destination.get("can_move_next", False),
                "from_address": previous_address,
                "google_maps_url": (
                    "https://www.google.com/maps/dir/?api=1"
                    f"&origin={quote(previous_address)}"
                    f"&destination={quote(address)}"
                ),
            }
        )
        previous_address = address

    return step_links


def _rebuild_origin_routes(origin) -> dict[int, Route]:
    dispatch_batch = origin.dispatch_batch
    if not dispatch_batch:
        return {}

    stops = list(
        dispatch_batch.stops.filter(route_number__isnull=False)
        .order_by("route_number", "stop_order", "id")
    )
    grouped_stops: dict[int, list[DispatchStop]] = {}
    for stop in stops:
        grouped_stops.setdefault(stop.route_number, []).append(stop)

    origin.relational_route.all().delete()

    routes_by_sequence = {}
    for normalized_sequence, original_sequence in enumerate(sorted(grouped_stops), start=1):
        group = grouped_stops[original_sequence]
        addresses = [stop.address for stop in group]
        route = origin.relational_route.create(
            path=_build_route_payload(origin.name, addresses),
            sequence_number=normalized_sequence,
        )
        routes_by_sequence[normalized_sequence] = route
        for stop_order, stop in enumerate(group, start=1):
            stop.route = route
            stop.route_number = normalized_sequence
            stop.stop_order = stop_order
            stop.status = DispatchStop.Statuses.ASSIGNED
            stop.save(update_fields=["route", "route_number", "stop_order", "status", "updated_at"])

    return routes_by_sequence


@login_required
def index(request):
    organization = request.user.organization
    favorite_places = []
    recent_places = []
    recent_batch_entries = []
    base_location_name = ""
    base_city = ""
    base_lat = ""
    base_lon = ""
    country_code = ""

    if organization:
        favorite_places = list(organization.saved_places.filter(is_favorite=True)[:4])
        recent_places = list(organization.saved_places.all()[:6])
        base_location_name = organization.base_location_name
        base_city = organization.base_city
        base_lat = organization.base_lat or ""
        base_lon = organization.base_lon or ""
        country_code = organization.country_code
        recent_batch_entries = _build_recent_batch_entries(organization)

    return render(
        request=request,
        template_name="RMapp/index.html",
        context={
            "organization_name": organization.name if organization else "",
            "base_location_name": base_location_name,
            "base_city": base_city,
            "base_lat": base_lat,
            "base_lon": base_lon,
            "country_code": country_code,
            "favorite_places": favorite_places,
            "recent_places": recent_places,
            "recent_batch_entries": recent_batch_entries,
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
            origin_object = get_coordinates_and_objects(origen, destinos, request.user.organization, created_by=request.user)
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
    country_bias = request.GET.get("country_bias", "").strip().lower()
    country_filter = request.GET.get("country_filter", "").strip().lower()

    if organization:
        country_bias = country_bias or organization.country_code
        if organization.base_lat is not None and organization.base_lon is not None:
            proximity = (float(organization.base_lon), float(organization.base_lat))

    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    if lat and lon:
        try:
            proximity = (float(lon), float(lat))
        except ValueError:
            pass

    try:
        remote_results = get_geocoding_client().autocomplete(
            query,
            country_bias=country_bias,
            country_filter=country_filter,
            city_bias=organization.base_city if organization else "",
            proximity=proximity,
        )
    except GeoapifyError as exc:
        if local_results:
            return JsonResponse({"results": local_results, "warning": str(exc)})
        return JsonResponse({"results": [], "error": str(exc)}, status=502)

    results = _merge_autocomplete_results(local_results, remote_results)
    return JsonResponse({"results": results})


@login_required
def move_stop(request, id: int, stop_id: int):
    if request.method != "POST":
        return HttpResponseRedirect(redirect_to=reverse("RMapp:routes", args=(id,)))

    route = get_object_or_404(
        Route.objects.select_related("origin", "origin__dispatch_batch"),
        pk=id,
        origin__organization=request.user.organization,
    )
    dispatch_batch = route.origin.dispatch_batch
    if not dispatch_batch:
        messages.error(request, "Esta ruta antigua todavía no pertenece a un despacho editable.")
        return HttpResponseRedirect(redirect_to=reverse("RMapp:routes", args=(route.id,)))

    stop = get_object_or_404(
        DispatchStop,
        pk=stop_id,
        batch=dispatch_batch,
        route=route,
    )
    direction = request.POST.get("direction")
    if direction not in {"previous", "next"}:
        messages.error(request, "Movimiento inválido.")
        return HttpResponseRedirect(redirect_to=reverse("RMapp:routes", args=(route.id,)))

    current_route_number = stop.route_number or route.sequence_number
    existing_route_numbers = list(
        dispatch_batch.stops.exclude(route_number__isnull=True).values_list("route_number", flat=True)
    )
    max_route_number = max(existing_route_numbers) if existing_route_numbers else current_route_number

    if direction == "previous":
        if current_route_number <= 1:
            messages.error(request, "La parada ya está en la primera ruta del despacho.")
            return HttpResponseRedirect(redirect_to=reverse("RMapp:routes", args=(route.id,)))
        target_route_number = current_route_number - 1
    else:
        target_route_number = current_route_number + 1 if current_route_number < max_route_number else max_route_number + 1

    with transaction.atomic():
        last_target_order = (
            dispatch_batch.stops.filter(route_number=target_route_number)
            .exclude(pk=stop.pk)
            .count()
        )
        stop.route_number = target_route_number
        stop.stop_order = last_target_order + 1
        stop.save(update_fields=["route_number", "stop_order", "updated_at"])
        rebuilt_routes = _rebuild_origin_routes(route.origin)

    target_route = rebuilt_routes.get(min(target_route_number, len(rebuilt_routes)))
    if not target_route:
        messages.error(request, "No fue posible reconstruir la ruta de destino.")
        return HttpResponseRedirect(redirect_to=reverse("RMapp:index"))

    messages.success(request, "La parada fue movida y el despacho quedó actualizado.")
    return HttpResponseRedirect(redirect_to=reverse("RMapp:routes", args=(target_route.id,)))


@login_required
def routes(request, id):
    route_0 = get_object_or_404(
        Route.objects.select_related("origin", "origin__dispatch_batch"),
        pk=id,
        origin__organization=request.user.organization,
    )
    origin = route_0.origin
    route_data = route_0.json_dic()
    route_entries, current_route_number = _build_route_entries(origin, route_0.id)
    dispatch_stops = []
    if origin.dispatch_batch:
        dispatch_stops = list(
            origin.dispatch_batch.stops.filter(route=route_0)
            .order_by("stop_order", "id")
        )

    if dispatch_stops:
        destinations = [stop.address for stop in dispatch_stops]
        step_link_data = [
            {
                "address": stop.address,
                "stop_id": stop.id,
                "can_move_previous": current_route_number > 1,
                "can_move_next": True,
            }
            for stop in dispatch_stops
        ]
    else:
        destinations = route_data["Destinos"][0]
        step_link_data = [{"address": address} for address in destinations]

    share_text = _build_share_text(current_route_number, route_data["Origin"], destinations)
    step_navigation_links = _build_step_navigation_links(route_data["Origin"], step_link_data)
    google_maps_directions_url = ""
    if len(destinations) <= 10:
        google_maps_directions_url = _build_google_maps_directions_url(route_data["Origin"], destinations)
    whatsapp_share_text = _build_whatsapp_share_text(
        current_route_number,
        route_data["Origin"],
        destinations,
        google_maps_directions_url,
    )

    return render(
        request=request,
        template_name="RMapp/cr.html",
        context={
            "Origin": origin,
            "Route": route_0,
            "dispatch_batch": origin.dispatch_batch,
            "organization_name": request.user.organization.name if request.user.organization else "",
            "route_destinations": destinations,
            "route_stop_count": len(destinations),
            "route_entries": route_entries,
            "current_route_number": current_route_number,
            "total_route_count": len(route_entries),
            "share_text": share_text,
            "share_text_urlencoded": quote(share_text),
            "whatsapp_share_text_urlencoded": quote(whatsapp_share_text),
            "google_maps_directions_url": google_maps_directions_url,
            "step_navigation_links": step_navigation_links,
        },
    )
