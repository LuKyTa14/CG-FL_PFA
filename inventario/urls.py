from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.productos_list, name='productos_list'),
    path('crear/', views.producto_create, name='producto_create'),
    path('editar/<int:pk>/', views.producto_edit, name='producto_edit'),
    path('eliminar/<int:pk>/', views.producto_delete, name='producto_delete'),
    path('stock/<int:pk>/', views.stock_update, name='stock_update'),
]