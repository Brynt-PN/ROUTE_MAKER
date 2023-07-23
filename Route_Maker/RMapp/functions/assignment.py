
import simplejson as json
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
    nodo.quadrant = equals[(lon,lat)]
    nodo.save()

def get_origin_distance(origin, nodo):
    #SQRT es la raiz cuadrada
    distance = sqrt((nodo.lon - origin.lon)**2 + (nodo.lat - origin.lat)**2)
    nodo.origin_distance = distance
    nodo.save()

def get_nodo_distance(nodo1, nodo2):
    distance = sqrt((nodo2.lon - nodo1.lon)**2 + (nodo2.lat - nodo1.lat)**2)
    return round(distance,8)

def compare_distance(dis1,dis2):
    return dis1<=dis2

def assign_quadrant_and_distance(origin):
        nodos = origin.relational_nodos.all()
        for nodo in nodos:
            compare(origin=origin,nodo=nodo)
            get_origin_distance(origin=origin,nodo=nodo)
            

def object_to_coordinates(data):
     lst_coordinates = []
     for nodo in data:
          nodo_dic = nodo.to_dic()
          lst_coordinates.append(nodo_dic)
     return lst_coordinates

def list_to_json(data):
    lst_dic = object_to_coordinates(data)
    json_data = json.dumps(lst_dic, use_decimal=True)
    return json_data

