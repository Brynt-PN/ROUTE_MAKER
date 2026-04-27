
import simplejson as json
from math import sqrt
from decimal import Decimal

equals = {
        (True,True):'I',
        (False,True):'II',
        (False,False):'III',
        (True,False):'IV'
    }

#Convercion de Objeto Maps a Origen y nodos
def Point_to_Origin(Origin_Point, organization, dispatch_batch=None):
     from ..models import Origin
     Origin_Object = Origin(
          name = Origin_Point['formatted_address'],
          lat  = Origin_Point['latitude'],
          lon  = Origin_Point['longitude'],
          dispatch_batch=dispatch_batch,
          organization=organization,
          )
     Origin_Object.save()
     return Origin_Object

def Points_to_Nodos(Destino_Points,Origin_Object, dispatch_batch=None):
     from ..models import DispatchStop
     for Point in Destino_Points:
        Nodo = Origin_Object.relational_nodos.create(
               name = Point['formatted_address'],
               lat  = Point['latitude'],
               lon  = Point['longitude']
          )
        Nodo.save()
        if dispatch_batch:
            DispatchStop.objects.create(
                batch=dispatch_batch,
                nodo=Nodo,
                address=Point['formatted_address'],
                lat=Point['latitude'],
                lon=Point['longitude'],
            )

def format_to_object(Origin_Point,Destino_Points, organization, dispatch_batch=None):
     Origin_Object = Point_to_Origin(Origin_Point, organization, dispatch_batch=dispatch_batch)
     Points_to_Nodos(Destino_Points,Origin_Object, dispatch_batch=dispatch_batch)
     return Origin_Object

#Define el cuadrante del nodo en función al origen y lo asigna
def compare(origin,nodo):
    origin_lon = Decimal(origin.lon)
    origin_lat = Decimal(origin.lat)
    nodo_lon = Decimal(nodo.lon)
    nodo_lat = Decimal(nodo.lat)
    lon = origin_lon < nodo_lon
    lat = origin_lat < nodo_lat
    nodo.quadrant = equals[(lon,lat)]
    nodo.save()

#Calcula la distancia del Nodo al Origen y la asigna
def get_origin_distance(origin, nodo):
    #SQRT es la raiz cuadrada
    distance = sqrt((Decimal(nodo.lon) - Decimal(origin.lon))**2 + (Decimal(nodo.lat) - Decimal(origin.lat))**2)
    nodo.origin_distance = distance
    nodo.save()

#Calcula la distancia entre dos nodos
def get_nodo_distance(nodo1, nodo2):
    distance = sqrt((Decimal(nodo2.lon) - Decimal(nodo1.lon))**2 + (Decimal(nodo2.lat) - Decimal(nodo1.lat))**2)
    decimal_distance = Decimal(str(distance))
    return round(decimal_distance,8)

#Comapra dos distancias
def compare_distance(dis1,dis2):
    return dis1<=dis2

#Recorre una lista de Nodos y les asigna su cuadrante y distancia al Origen
def assign_quadrant_and_distance(origin):
        nodos = origin.relational_nodos.all()
        for nodo in nodos:
            compare(origin=origin,nodo=nodo)
            get_origin_distance(origin=origin,nodo=nodo)

#Combertimos la Lista de Objetos en un Dic
def get_route_dic(List):
     Nodos = []
     route_dic = {
          'Origin'   : List[0].name,
          'Destinos' : [Nodos]
     }
     for Nodo in List[1:]:
          Nodos.append(Nodo.name)
     return route_dic
    
#Convierte una ruta en formato DIC a JSON
def dic_to_json(data):
    json_data = json.dumps(data, use_decimal=True,ensure_ascii=False)#Ensure_ascii es para mantener las tildes y otros caracteres
    return json_data

