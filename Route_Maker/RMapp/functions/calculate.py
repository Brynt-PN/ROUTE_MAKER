from math import atan2, ceil, pi

from .assignment import assign_quadrant_and_distance, dic_to_json, format_to_object, get_nodo_distance, get_route_dic
from ..providers.geoapify import get_geocoding_client


def get_coordinates_and_objects(Origen, Destinos, organization, created_by=None):
    from ..models import DispatchBatch

    geocoder = get_geocoding_client()
    Origin_Point = geocoder.geocode(Origen)
    Destino_Points = [geocoder.geocode(Destino) for Destino in Destinos]
    dispatch_batch = DispatchBatch.objects.create(
        organization=organization,
        created_by=created_by,
        origin_address=Origin_Point["formatted_address"],
        total_stops=len(Destino_Points),
    )
    Origin_Object = format_to_object(Origin_Point, Destino_Points, organization, dispatch_batch=dispatch_batch)
    return Origin_Object


def _node_angle(origin, nodo):
    return atan2(float(nodo.lat) - float(origin.lat), float(nodo.lon) - float(origin.lon))


def _rotate_nodes_by_gap(origin, nodos):
    if len(nodos) <= 1:
        return list(nodos)

    ordered = sorted(
        nodos,
        key=lambda nodo: (
            _node_angle(origin, nodo),
            float(nodo.origin_distance),
            nodo.id,
        ),
    )
    angles = [_node_angle(origin, nodo) for nodo in ordered]
    split_index = 0
    largest_gap = -1.0

    for index, angle in enumerate(angles):
        next_angle = angles[(index + 1) % len(angles)]
        if index == len(angles) - 1:
            next_angle += 2 * pi
        gap = next_angle - angle
        if gap > largest_gap:
            largest_gap = gap
            split_index = (index + 1) % len(ordered)

    return ordered[split_index:] + ordered[:split_index]


def _balanced_group_sizes(total_stops, max_stops_per_route):
    route_count = max(1, ceil(total_stops / max_stops_per_route))
    base_size = total_stops // route_count
    remainder = total_stops % route_count
    return [base_size + (1 if index < remainder else 0) for index in range(route_count)]


def _nearest_neighbor_sequence(origin, nodos):
    ordered = []
    remaining = list(nodos)
    current = origin

    while remaining:
        next_nodo = min(
            remaining,
            key=lambda nodo: (
                float(get_nodo_distance(current, nodo)),
                float(nodo.origin_distance),
                nodo.id,
            ),
        )
        ordered.append(next_nodo)
        remaining.remove(next_nodo)
        current = next_nodo

    return ordered


def _route_cost(origin, nodos):
    total = 0.0
    current = origin
    for nodo in nodos:
        total += float(get_nodo_distance(current, nodo))
        current = nodo
    return total


def _two_opt(origin, nodos):
    if len(nodos) < 4:
        return list(nodos)

    best = list(nodos)
    best_cost = _route_cost(origin, best)
    improved = True

    while improved:
        improved = False
        for start in range(len(best) - 2):
            for end in range(start + 1, len(best) - 1):
                candidate = best[:start] + list(reversed(best[start : end + 1])) + best[end + 1 :]
                candidate_cost = _route_cost(origin, candidate)
                if candidate_cost + 1e-9 < best_cost:
                    best = candidate
                    best_cost = candidate_cost
                    improved = True
                    break
            if improved:
                break

    return best


def _build_route_groups(origin, nodos, max_stops_per_route):
    rotated_nodes = _rotate_nodes_by_gap(origin, nodos)
    group_sizes = _balanced_group_sizes(len(rotated_nodes), max_stops_per_route)
    groups = []
    offset = 0

    for size in group_sizes:
        groups.append(rotated_nodes[offset : offset + size])
        offset += size

    return groups


def create_route(origin):
    assign_quadrant_and_distance(origin)
    max_stops_per_route = 8
    if origin.organization and origin.organization.max_stops_per_route:
        max_stops_per_route = origin.organization.max_stops_per_route

    nodos = list(origin.relational_nodos.all())
    route_sequence = 0

    for group in _build_route_groups(origin, nodos, max_stops_per_route):
        sequenced_group = _two_opt(origin, _nearest_neighbor_sequence(origin, group))
        route = [origin, *sequenced_group]
        route_sequence += 1
        route_dic = get_route_dic(route)
        route_json = dic_to_json(route_dic)
        route_object = origin.relational_route.create(path=route_json, sequence_number=route_sequence)
        for stop_order, nodo in enumerate(sequenced_group, start=1):
            nodo.has_route = True
            nodo.save(update_fields=["has_route"])
            if hasattr(nodo, "dispatch_stop"):
                nodo.dispatch_stop.route = route_object
                nodo.dispatch_stop.route_number = route_sequence
                nodo.dispatch_stop.stop_order = stop_order
                nodo.dispatch_stop.status = nodo.dispatch_stop.Statuses.ASSIGNED
                nodo.dispatch_stop.save(update_fields=["route", "route_number", "stop_order", "status", "updated_at"])

    if origin.dispatch_batch:
        origin.dispatch_batch.status = origin.dispatch_batch.Statuses.GENERATED
        origin.dispatch_batch.algorithm_version = "heuristic-sweep-v2"
        origin.dispatch_batch.save(update_fields=["status", "algorithm_version", "updated_at"])
    return origin.relational_route.order_by("sequence_number", "id").first()
