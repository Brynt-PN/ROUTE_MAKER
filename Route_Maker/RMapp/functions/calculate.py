
from math import sqrt

Origin = {
    'lon' : 0.0,
    'lat' : 0.0
}

Nodo_A = {
    'lon' : 0.68,
    'lat' : 0.58
}

Nodo_B = {
    'lon' : 0.74,
    'lat' : 2.11
}

Nodo_C = {
    'lon' : 2.52,
    'lat' : 1.8
}

Nodo_D = {
    'lon' : 3.54,
    'lat' : 2.79
}

Nodo_E = {
    'lon' : 2.29,
    'lat' : 3.77
}

Nodo_F = {
    'lon' : 4.4,
    'lat' : 4.09
}

nodos = [Nodo_A,Nodo_B,Nodo_C,Nodo_D,Nodo_E,Nodo_F]

def get_distance(origin, nodo):
    distance = sqrt((nodo['lon'] - origin['lon'])**2 + (nodo['lat'] - origin['lat'])**2)
    return (nodo,distance)

def compare_distance(dis1,dis2):
    return dis1<dis2

distances = [get_distance(Origin,nodo)for nodo in nodos]
#Aqui utilizamos una lambda para acceder al segundo elemento de la tupla
# que contiene la distancia
ordered_distance = sorted(distances, key = lambda x: x[1])

ordered_nodes_distance = ordered_distance

route = []

i = 0

for nodo_distance in ordered_nodes_distance:
    if route is None:
        route = route + nodo_distance[0]
        i += 1
    else:        
        distance = get_distance(nodo_distance[0],ordered_nodes_distance[(i+1)][0])
        assignmet_route = compare_distance(distance[1],nodo_distance[1])





print(ordered_distance)


