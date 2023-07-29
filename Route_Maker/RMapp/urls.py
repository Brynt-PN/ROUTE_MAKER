from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create_routes/', views.create_routes, name='create_routes'),
]
