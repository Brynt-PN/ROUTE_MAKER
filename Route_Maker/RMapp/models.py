from django.db import models
from .functions.calculate import  create_route

# Create your models here.
class Origin(models.Model):
    name = models.CharField(max_length=200)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    
    def __str__(self) -> str:
        return self.name
    
    def to_dic(self):
        dic_data = {
            "latitude": float(self.lat),
            "longitude": float(self.lon)
        }
        return dic_data
            
    def define_all_routes(self):
        create_route(self)
    
class Nodo(models.Model):
    name = models.CharField(max_length=200)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    #Aqui renombramos el Qeryset, que guarda la relacion de 1 a muchos
    #que existe entre Origin y Nodo, usando relate_name
    origin = models.ForeignKey(Origin,on_delete=models.CASCADE,
                             related_name='relational_nodos')
    quadrant = models.CharField(max_length=3)
    origin_distance = models.DecimalField(max_digits=18, decimal_places=8, default=0.0)
    has_route = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name
    def to_dic(self):
        dic_data = {
            "latitude": float(self.lat),
            "longitude": float(self.lon)
        }
        return dic_data

class Route(models.Model):
    path = models.JSONField()
    origin = models.ForeignKey(Origin,on_delete=models.CASCADE,
                             related_name='relational_route')

    def __str__(self) -> str:
        return self.path

