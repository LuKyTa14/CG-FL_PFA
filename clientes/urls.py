from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.clientes_list, name='clientes_list'),
    path('crear/', views.cliente_create, name='cliente_create'),
    path('editar/<int:pk>/', views.cliente_edit, name='cliente_edit'),
    path('eliminar/<int:pk>/', views.cliente_delete, name='cliente_delete'),
    path('cuentas-corrientes/', views.cuenta_corriente_list, name='cuenta_corriente_list'),
    path('cuentas-corrientes/<int:pk>/', views.cuenta_corriente_detalle, name='cuenta_corriente_detalle'),
]