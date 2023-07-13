
from math import sqrt

def get_origin_distance(origin, nodo):
    #SQRT es la raiz cuadrada
    distance = sqrt((nodo.lon - origin.lon)**2 + (nodo.lat - origin.lat)**2)
    nodo.origin_distance = distance
    nodo.save()

def get_nodo_distance(nodo1, nodo2):
    distance = sqrt((nodo2.lon - nodo1.lon)**2 + (nodo2.lat - nodo2.lat)**2)
    return distance

def compare_distance(dis1,dis2):
    return dis1<=dis2

def create_route(origin):

    origin.assign_quadrant_and_distance()
    #Aqui utilizamos una lambda para acceder al origin_distance del nodo para ordenarlo
    ordered_nodes_distance = sorted(origin.relational_nodos.filter(has_route = False),
                            key = lambda x: x.origin_distance)

    route = [origin]

    for nodo in ordered_nodes_distance:    

        nodo_distance = get_nodo_distance(route[-1], nodo)
        assignmet_route = compare_distance(nodo_distance, nodo.origin_distance)
        if assignmet_route == True:
            route.append(nodo)
            
    print(route)








