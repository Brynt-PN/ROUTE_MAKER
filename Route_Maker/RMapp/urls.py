from django.urls import path
from . import views

app_name = 'RMapp'#Nos permite referenciar en las Templates
urlpatterns = [
    path('', views.index, name='index'),
    path('create_routes/', views.create_routes, name='create_routes'),
    path('<int:id>/', views.routes, name='routes'),
]
