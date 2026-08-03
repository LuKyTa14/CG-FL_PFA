from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.ventas_list, name='ventas_list'),
    path('nueva/', views.venta_create, name='venta_create'),
    path('detalle/<int:pk>/', views.venta_detalle, name='venta_detalle'),
    path('finalizar/<int:pk>/', views.venta_finalizar, name='venta_finalizar'),
    path('cancelar/<int:pk>/', views.venta_cancelar, name='venta_cancelar'),
    path('comprobante/<int:pk>/', views.venta_comprobante, name='venta_comprobante'),
]