


origin = {
    'lon':0.0,
    'lat':0.0
}

nodo_A = {
    'lon':1.12,
    'lat':1.64
}

nodo_B = {
    'lon':-3.51,
    'lat':2.37
}

nodo_C = {
    'lon':-2.49,
    'lat':-1.38
}

nodo_D = {
    'lon':3.17,
    'lat':-1.6
}

ponits = [nodo_A,nodo_B,nodo_C,nodo_D]

Cuadrantes = {}

equals = {
        (True,True):'I',
        (False,True):'II',
        (False,False):'III',
        (True,False):'IV'
    }

for i in ponits:
    lon = origin['lon'] < i['lon']
    lat = origin['lat'] < i['lat']
    Cuadrantes[tuple(i.items())] = equals[(lon,lat)]

print(Cuadrantes)
