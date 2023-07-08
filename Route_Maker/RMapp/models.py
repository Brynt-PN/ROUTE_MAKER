from django.db import models

# Create your models here.
class Nodo(models.Model):
    name = models.CharField(max_length=200)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    cuadrante = models.CharField(max_length=2)

    def __str__(self) -> str:
        return self.name
    
class Origin(models.Model):
    name = models.CharField(max_length=200)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    
    def __str__(self) -> str:
        return self.name

class Route(models.Model):
    path = models.JSONField()

    def __str__(self) -> str:
        return self.path
