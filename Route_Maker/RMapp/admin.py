from django.contrib import admin
from .models import Origin, Nodo, Route
# Register your models here.

admin.site.register(Origin)
admin.site.register(Nodo)
admin.site.register(Route)