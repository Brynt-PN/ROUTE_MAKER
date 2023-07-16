
from json import dumps
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

def get_nodo_distance(nodo1, nodo2):
    distance = sqrt((nodo2.lon - nodo1.lon)**2 + (nodo2.lat - nodo1.lat)**2)
    return distance

def compare_distance(dis1,dis2):
    return dis1<=dis2

def assign_quadrant_and_distance(origin):
        nodos = origin.relational_nodos.all()
        for nodo in nodos:
            quadrant = compare(origin=origin,nodo=nodo)
            get_origin_distance(origin=origin,nodo=nodo)
            nodo.quadrant = quadrant
            nodo.save()

def object_to_coordinates(object):
     coordinates = {
          'name' : object.name,
          'lon'  : object.lon,
          'lat'  : object.lat
     }
     return coordinates

def list_to_json(list):
     json_data = dumps(list, default=object_to_coordinates)
     return json_data