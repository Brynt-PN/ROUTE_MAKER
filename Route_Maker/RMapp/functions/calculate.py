
from .assignment import assign_quadrant_and_distance, get_nodo_distance,compare_distance,list_to_json

def create_route(origin):
    assign_quadrant_and_distance(origin)

    #EXISTS() nos permite verificar que este query set exista.
    while origin.relational_nodos.filter(has_route = False).exists():

        #Aqui utilizamos una lambda para acceder al origin_distance del nodo para ordenarlo
        ordered_nodes_distance = sorted(origin.relational_nodos.filter(has_route = False),
                                key = lambda x: x.origin_distance)

        route = [origin]

        for nodo in ordered_nodes_distance:    

            nodo_distance = get_nodo_distance(route[-1], nodo)
            assignmet_route = compare_distance(nodo_distance, nodo.origin_distance)
            print(f'Nodo anterior {route[-1]}, Nodo evaluado {nodo}')
            print(f'Distancia de nodo a nodo {nodo_distance}')
            print(f'Distancia de Origen a Nodo {nodo.origin_distance}')
            if assignmet_route == True:
                route.append(nodo)
                nodo.has_route = True
                nodo.save()
        
        route_json = list_to_json(route)
        origin.relational_route.create(path = route_json)

            
    print(origin.relational_route.all())










