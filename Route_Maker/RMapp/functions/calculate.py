from .assignment import assign_quadrant_and_distance, get_nodo_distance,compare_distance,dic_to_json,format_to_object,get_route_dic
from ..providers.geoapify import get_geocoding_client

#Obtener coordenadas a partir de direcciones y guardarlas en Objetos Origin y Nodo
def get_coordinates_and_objects(Origen, Destinos, organization):
    geocoder = get_geocoding_client()
    Origin_Point = geocoder.geocode(Origen)
    Destino_Points = [geocoder.geocode(Destino) for Destino in Destinos]
    Origin_Object = format_to_object(Origin_Point,Destino_Points, organization)
    return Origin_Object


#Crear el Objeto Ruta
def create_route(origin):
    assign_quadrant_and_distance(origin)
    #Verificamos si existen Nodos que no tienen una ruta asignada
    while origin.relational_nodos.filter(has_route = False).exists():#EXISTS() verifica que el queryset exista.
        #Obtenemos la sita de Nodos sin Ruta asignada
        ordered_nodes_distance = sorted(origin.relational_nodos.filter(has_route = False),
                                key = lambda x: x.origin_distance)#Ordenamos segun su Distancia al Origen con una Lambda
        route = [origin]#Creamos la ruta y agregamos el Origen
        #Recorremos la lista de Nodos y verificamos si se agregan o no a la Ruta
        for nodo in ordered_nodes_distance:    
            nodo_distance = get_nodo_distance(route[-1], nodo)
            assignmet_route = compare_distance(nodo_distance, nodo.origin_distance)
            if assignmet_route == True:
                route.append(nodo)
                nodo.has_route = True
                nodo.save()
        #Pasamos la Ruta para combertirla en un Objeto Route
        route_dic = get_route_dic(route)
        route_json = dic_to_json(route_dic)
        #Creamos el Objeto Ruta relacionado a el Origen
        origin.relational_route.create(path = route_json)
    Routes = origin.relational_route.all()
    return Routes[0]




    















