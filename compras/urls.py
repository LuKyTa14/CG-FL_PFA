from django.urls import path
from . import views

app_name = 'compras'

urlpatterns = [
    path('', views.compras_list, name='compras_list'),
    path('nueva/', views.compra_create, name='compra_create'),
    path('detalle/<int:pk>/', views.compra_detalle, name='compra_detalle'),
    path('finalizar/<int:pk>/', views.compra_finalizar, name='compra_finalizar'),
    path('cancelar/<int:pk>/', views.compra_cancelar, name='compra_cancelar'),
    path('crear-producto-agil/', views.producto_rapido_desde_compra, name='producto_rapido_desde_compra'),
    path('crear-producto-agil/<int:compra_pk>/', views.producto_rapido_desde_compra, name='producto_rapido_desde_compra'),
    path('comprobante/<int:pk>/', views.compra_comprobante, name='compra_comprobante'),
]