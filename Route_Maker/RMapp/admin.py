from django.contrib import admin
from .models import Origin, Nodo, Route, SavedPlace
# Register your models here.

admin.site.register(Origin)
admin.site.register(Nodo)
admin.site.register(Route)
admin.site.register(SavedPlace)
