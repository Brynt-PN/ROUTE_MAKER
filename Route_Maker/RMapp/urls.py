from django.urls import path
from . import views

app_name = 'RMapp'#Nos permite referenciar en las Templates
urlpatterns = [
    path('', views.index, name='index'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),
    path('create_routes/', views.create_routes, name='create_routes'),
    path('<int:id>/stops/<int:stop_id>/move/', views.move_stop, name='move_stop'),
    path('<int:id>/', views.routes, name='routes'),
]
