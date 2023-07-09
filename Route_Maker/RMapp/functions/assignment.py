
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

