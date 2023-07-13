from django.db import models
from .functions.assignment import compare
from .functions.calculate import get_origin_distance

# Create your models here.
class Origin(models.Model):
    name = models.CharField(max_length=200)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    
    def __str__(self) -> str:
        return self.name
    
    def assign_quadrant_and_distance(self):
        nodos = self.relational_nodos.all()
        for nodo in nodos:
            quadrant = compare(origin=self,nodo=nodo)
            get_origin_distance(origin=self,nodo=nodo)
            nodo.quadrant = quadrant
            #No olvides que sin Save los cambios se pierden
            nodo.save()
    
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
    #Esto nos ayudara a determinar que nodulos estan libres para nuevas rutas
    has_route = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

class Route(models.Model):
    path = models.JSONField()
    origin = models.ForeignKey(Origin,on_delete=models.CASCADE,
                             related_name='relational_route')

    def __str__(self) -> str:
        return self.path
