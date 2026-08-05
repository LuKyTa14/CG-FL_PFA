from django.urls import path
from . import views

app_name = 'contabilidad'

urlpatterns = [
    path('dashboard/', views.dashboard_contabilidad, name='dashboard_contabilidad'),
    
    path('cierre/nuevo/', views.cierre_caja_create, name='cierre_caja_create'),
    path('historial/', views.historial_cierres, name='historial_cierres'),
    path('arqueo/<int:cierre_id>/imprimir/', views.imprimir_arqueo, name='imprimir_arqueo'),
]