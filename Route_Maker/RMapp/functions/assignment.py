
from math import sqrt

equals = {
        (True,True):'I',
        (False,True):'II',
        (False,False):'III',
        (True,False):'IV'
    }

def compare(origin,nodo):
    lon = origin.lon < nodo.lon
    lat = origin.lat < nodo.lat
    return equals[(lon,lat)]

def get_origin_distance(origin, nodo):
    #SQRT es la raiz cuadrada
    distance = sqrt((nodo.lon - origin.lon)**2 + (nodo.lat - origin.lat)**2)
    nodo.origin_distance = distance
    nodo.save()

def assign_quadrant_and_distance(origin):
        nodos = origin.relational_nodos.all()
        for nodo in nodos:
            quadrant = compare(origin=origin,nodo=nodo)
            get_origin_distance(origin=origin,nodo=nodo)
            nodo.quadrant = quadrant
            nodo.save()