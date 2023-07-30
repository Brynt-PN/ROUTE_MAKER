
import requests
import polyline
from datetime import datetime

#Datos contantes
url = 'https://routes.googleapis.com/directions/v2:computeRoutes'

headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": "AIzaSyA6Z9NAXTqYc8S0HFYWpLDYdnoFS9BNeAI",
    "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
}

Time_now = datetime.now()
Time_data = Time_now.strftime("%Y-%m-%dT%H:%M:%SZ")

#Creación de la DATA para la Solicitud a partir de la Lista de Objetos enrutados
def Origin_converse_data_route(List_Route):
    Origin = List_Route[0]
    origin = {
        "location": {
            "latLng": {
                "latitude": Origin.lat,
                "longitude": Origin.lon
            }
        }
    }
    return origin

def Destino_converse_data_route(List_Route):
    Nodo = List_Route[-1]
    Destino = {
        "location": {
            "latLng": {
                "latitude": Nodo.lat,
                "longitude": Nodo.lon
            }
        }
    }
    return Destino

def Wapoints_converse_data_route(List_Route):
    Wapoints = []
    for Destino in List_Route[1:-1]:
        wapoint = {
            "location": {
                "latLng": {
                    "latitude": Destino.lat,
                    "longitude": Destino.lon
                }
            }
        }
        Wapoints.append(wapoint)
    return Wapoints

def create_body_data(List_Route):
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

#Dando formato a la Respuesta
def response_route(List_Route, Route, Decode_Polyline):
    response = {
        'Ruta'       : List_Route,
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
        return f'Error en la solicitud, status code {response.status_code}'
        



