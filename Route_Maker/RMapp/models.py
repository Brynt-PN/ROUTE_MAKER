from django.db import models
from functions.assignment import compare

# Create your models here.
class Origin(models.Model):
    name = models.CharField(max_length=200)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    
    def __str__(self) -> str:
        return self.name
    
    def assign_quadrant(self):
        nodos = self.relational_nodos.all()
        nodos_list = []
        for nodo in nodos:
            quadrant = compare(origin=self,nodo=nodo)
            nodo.quadrant = quadrant
            nodos_list.append((nodo,nodo.quadrant))
        return nodos_list
    
class Nodo(models.Model):
    name = models.CharField(max_length=200)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    origin = models.ForeignKey(Origin,on_delete=models.CASCADE, related_name='relational_nodos')
    quadrant = models.CharField(max_length=2)

    def __str__(self) -> str:
        return self.name

class Route(models.Model):
    path = models.JSONField()

    def __str__(self) -> str:
        return self.path
