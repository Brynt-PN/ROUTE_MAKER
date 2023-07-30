
import requests
import polyline
import json
from datetime import datetime, timedelta

#Datos contantes
url = 'https://routes.googleapis.com/directions/v2:computeRoutes'

headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": "AIzaSyA6Z9NAXTqYc8S0HFYWpLDYdnoFS9BNeAI",
    "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
}

Time_now = datetime.now()
Time_future = Time_now + timedelta(minutes=10)
Time_data = Time_future.strftime("%Y-%m-%dT%H:%M:%SZ")

#Creación de la DATA para la Solicitud a partir de la Lista de Objetos enrutados
def Origin_converse_data_route(List_Route):
    Origin = List_Route[0]
    origin = {
        "location": {
            "latLng": Origin.to_dic()
        }
    }
    return origin

def Destino_converse_data_route(List_Route):
    Nodo = List_Route[-1]
    Destino = {
        "location": {
            "latLng": Nodo.to_dic()
        }
    }
    return Destino

def Wapoints_converse_data_route(List_Route):
    Wapoints = []
    for Destino in List_Route[1:-1]:
        wapoint = {
            "location": {
                "latLng": Destino.to_dic()
            }
        }
        Wapoints.append(wapoint)
    return Wapoints

def create_body_data(List_Route):
    if len(List_Route) >= 3:
        data = {
            
                "origin": Origin_converse_data_route(List_Route),
                "destination": Destino_converse_data_route(List_Route),
                "waypoints": Wapoints_converse_data_route(List_Route),
                "travelMode": "DRIVE",
                "routingPreference": "TRAFFIC_AWARE",
                "departureTime": Time_data,
                "computeAlternativeRoutes": False,
                "routeModifiers": {
                    "avoidTolls": False,
                    "avoidHighways": False,
                    "avoidFerries": False
                },
                "languageCode": "en-US",
                "units": "IMPERIAL"
            
        }
        return data
    else:
        data = {
            
                "origin": Origin_converse_data_route(List_Route),
                "destination": Destino_converse_data_route(List_Route),
                "travelMode": "DRIVE",
                "routingPreference": "TRAFFIC_AWARE",
                "departureTime": Time_data,
                "computeAlternativeRoutes": False,
                "routeModifiers": {
                    "avoidTolls": False,
                    "avoidHighways": False,
                    "avoidFerries": False
                },
                "languageCode": "en-US",
                "units": "IMPERIAL"
        
        }
        return data

#Dando formato a la Respuesta
def response_route(List_Route, Route, Decode_Polyline):
    List_Objects = [str(Object_Model.name) for Object_Model in List_Route]    
    response = {
        'Ruta'       : List_Objects,
        'Data_Route' : Route,
        'Polyline'   : Decode_Polyline
    }
    return response

#Obteniendo ruta de Google Maps
def get_route(List_Route):
    Data_Route = create_body_data(List_Route)
    response = requests.post(url=url, json=Data_Route, headers=headers)
    if response.status_code == 200:
        Route = response.json()
        encode_polyline = Route['routes'][0]['polyline']['encodedPolyline']
        decode_polyline = polyline.decode(encode_polyline)
        Route_response = response_route(List_Route,Route,decode_polyline)
        return Route_response
    else:
        # Si hay un error, mostrar el código de estado y el mensaje de error de la API de Google Maps
        return f"ERROR : {response.status_code} TYPO : {type(Data_Route)} CUERPO : {Data_Route} RESPUESTA : {response.text}"
        



