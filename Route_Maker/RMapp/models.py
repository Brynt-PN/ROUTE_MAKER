from django.db import models
from .functions.calculate import  create_route
import simplejson as json

# Create your models here.
class Origin(models.Model):
    name = models.CharField(max_length=200)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='origins',
        null=True,
        blank=True,
    )
    
    def __str__(self) -> str:
        return self.name
    
    def to_dic(self):
        dic_data = {
            "latitude": float(self.lat),
            "longitude": float(self.lon)
        }
        return dic_data
            
    def define_all_routes(self):
        return create_route(self)
    
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
    
    def json_dic(self):
     Dic = json.loads(self.path)
     return Dic


class SavedPlace(models.Model):
    class PlaceKinds(models.TextChoices):
        ORIGIN = "origin", "Origin"
        DESTINATION = "destination", "Destination"

    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='saved_places'
    )
    label = models.CharField(max_length=120, blank=True)
    address = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    place_kind = models.CharField(
        max_length=20,
        choices=PlaceKinds.choices,
        default=PlaceKinds.DESTINATION,
    )
    is_favorite = models.BooleanField(default=False)
    usage_count = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_favorite", "-usage_count", "-last_used_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "address", "place_kind"],
                name="unique_saved_place_per_org_and_kind",
            )
        ]

    def __str__(self) -> str:
        return self.label or self.address


