from .assignment import assign_quadrant_and_distance, get_nodo_distance,compare_distance,dic_to_json,format_to_object,get_route_dic
from ..providers.geoapify import get_geocoding_client

#Obtener coordenadas a partir de direcciones y guardarlas en Objetos Origin y Nodo
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
    Origin_Object = format_to_object(Origin_Point,Destino_Points, organization, dispatch_batch=dispatch_batch)
    return Origin_Object


#Crear el Objeto Ruta
def create_route(origin):
    assign_quadrant_and_distance(origin)
    max_stops_per_route = 8
    if origin.organization and origin.organization.max_stops_per_route:
        max_stops_per_route = origin.organization.max_stops_per_route
    route_sequence = 0
    #Verificamos si existen Nodos que no tienen una ruta asignada
    while origin.relational_nodos.filter(has_route = False).exists():#EXISTS() verifica que el queryset exista.
        #Obtenemos la sita de Nodos sin Ruta asignada
        ordered_nodes_distance = sorted(origin.relational_nodos.filter(has_route = False),
                                key = lambda x: x.origin_distance)#Ordenamos segun su Distancia al Origen con una Lambda
        route = [origin]#Creamos la ruta y agregamos el Origen
        #Recorremos la lista de Nodos y verificamos si se agregan o no a la Ruta
        for nodo in ordered_nodes_distance:    
            if len(route) - 1 >= max_stops_per_route:
                break
            nodo_distance = get_nodo_distance(route[-1], nodo)
            assignmet_route = compare_distance(nodo_distance, nodo.origin_distance)
            if assignmet_route == True:
                route.append(nodo)
                nodo.has_route = True
                nodo.save()
        #Pasamos la Ruta para combertirla en un Objeto Route
        route_sequence += 1
        route_dic = get_route_dic(route)
        route_json = dic_to_json(route_dic)
        #Creamos el Objeto Ruta relacionado a el Origen
        route_object = origin.relational_route.create(path=route_json, sequence_number=route_sequence)
        for stop_order, nodo in enumerate(route[1:], start=1):
            if hasattr(nodo, "dispatch_stop"):
                nodo.dispatch_stop.route = route_object
                nodo.dispatch_stop.route_number = route_sequence
                nodo.dispatch_stop.stop_order = stop_order
                nodo.dispatch_stop.status = nodo.dispatch_stop.Statuses.ASSIGNED
                nodo.dispatch_stop.save(update_fields=["route", "route_number", "stop_order", "status", "updated_at"])

    if origin.dispatch_batch:
        origin.dispatch_batch.status = origin.dispatch_batch.Statuses.GENERATED
        origin.dispatch_batch.save(update_fields=["status", "updated_at"])
    return origin.relational_route.order_by("sequence_number", "id").first()




    















