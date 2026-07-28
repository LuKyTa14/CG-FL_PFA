from django.urls import path
from . import views

app_name = 'proveedores'

urlpatterns = [
    path('', views.proveedores_list, name='proveedores_list'),
    path('crear/', views.proveedor_create, name='proveedor_create'),
    path('editar/<int:pk>/', views.proveedor_edit, name='proveedor_edit'),
    path('eliminar/<int:pk>/', views.proveedor_delete, name='proveedor_delete'),
]