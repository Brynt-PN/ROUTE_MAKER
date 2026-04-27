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


def _ordered_nodes_by_angle(origin, nodos):
    return sorted(
        nodos,
        key=lambda nodo: (
            _node_angle(origin, nodo),
            float(nodo.origin_distance),
            nodo.id,
        ),
    )


def _best_gap_split_index(origin, ordered):
    if len(ordered) <= 1:
        return 0

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

    return split_index


def _balanced_group_sizes(total_stops, max_stops_per_route):
    route_count = max(1, ceil(total_stops / max_stops_per_route))
    base_size = total_stops // route_count
    remainder = total_stops % route_count
    return [base_size + (1 if index < remainder else 0) for index in range(route_count)]


def _partition_by_sizes(nodes, group_sizes):
    groups = []
    offset = 0
    for size in group_sizes:
        groups.append(nodes[offset : offset + size])
        offset += size
    return groups


def _iter_partition_candidates(origin, nodos, max_stops_per_route):
    ordered = _ordered_nodes_by_angle(origin, nodos)
    group_sizes = _balanced_group_sizes(len(ordered), max_stops_per_route)
    yielded = set()

    candidate_orders = []
    if ordered:
        best_gap_index = _best_gap_split_index(origin, ordered)
        candidate_orders.append(ordered[best_gap_index:] + ordered[:best_gap_index])
        for rotation in range(len(ordered)):
            candidate_orders.append(ordered[rotation:] + ordered[:rotation])
        reversed_order = list(reversed(ordered))
        best_gap_index_reversed = _best_gap_split_index(origin, reversed_order)
        candidate_orders.append(reversed_order[best_gap_index_reversed:] + reversed_order[:best_gap_index_reversed])
        for rotation in range(len(reversed_order)):
            candidate_orders.append(reversed_order[rotation:] + reversed_order[:rotation])

    for candidate_order in candidate_orders:
        signature = tuple(nodo.id for nodo in candidate_order)
        if signature in yielded:
            continue
        yielded.add(signature)
        yield _partition_by_sizes(candidate_order, group_sizes)


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


def _optimize_group(origin, group):
    return _two_opt(origin, _nearest_neighbor_sequence(origin, group))


def _solution_score(origin, route_groups):
    route_costs = [_route_cost(origin, group) for group in route_groups]
    total_cost = sum(route_costs)
    max_cost = max(route_costs, default=0.0)
    min_size = min((len(group) for group in route_groups), default=0)
    max_size = max((len(group) for group in route_groups), default=0)
    size_penalty = (max_size - min_size) * 0.5
    return total_cost + (max_cost * 0.35) + size_penalty


def _build_best_route_groups(origin, nodos, max_stops_per_route):
    best_groups = []
    best_score = None

    for candidate_groups in _iter_partition_candidates(origin, nodos, max_stops_per_route):
        optimized_groups = [_optimize_group(origin, group) for group in candidate_groups if group]
        score = _solution_score(origin, optimized_groups)
        if best_score is None or score < best_score:
            best_groups = optimized_groups
            best_score = score

    return best_groups


def create_route(origin):
    assign_quadrant_and_distance(origin)
    max_stops_per_route = 8
    if origin.organization and origin.organization.max_stops_per_route:
        max_stops_per_route = origin.organization.max_stops_per_route

    nodos = list(origin.relational_nodos.all())
    route_groups = _build_best_route_groups(origin, nodos, max_stops_per_route)

    for sequence_number, group in enumerate(route_groups, start=1):
        route = [origin, *group]
        route_dic = get_route_dic(route)
        route_json = dic_to_json(route_dic)
        route_object = origin.relational_route.create(path=route_json, sequence_number=sequence_number)
        for stop_order, nodo in enumerate(group, start=1):
            nodo.has_route = True
            nodo.save(update_fields=["has_route"])
            if hasattr(nodo, "dispatch_stop"):
                nodo.dispatch_stop.route = route_object
                nodo.dispatch_stop.route_number = sequence_number
                nodo.dispatch_stop.stop_order = stop_order
                nodo.dispatch_stop.status = nodo.dispatch_stop.Statuses.ASSIGNED
                nodo.dispatch_stop.save(update_fields=["route", "route_number", "stop_order", "status", "updated_at"])

    if origin.dispatch_batch:
        origin.dispatch_batch.status = origin.dispatch_batch.Statuses.GENERATED
        origin.dispatch_batch.algorithm_version = "heuristic-sweep-v3"
        origin.dispatch_batch.save(update_fields=["status", "algorithm_version", "updated_at"])
    return origin.relational_route.order_by("sequence_number", "id").first()
