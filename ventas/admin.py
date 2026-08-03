from django.contrib import admin
from .models import Venta, DetalleVenta

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'sucursal', 'fecha_venta', 'estado', 'total', 'cajero')
    list_filter = ('estado', 'sucursal', 'metodo_pago', 'fecha_venta')
    search_fields = ('cliente__nombre', 'cliente__apellido', 'cliente__numero_documento')
    readonly_fields = ('fecha_venta', 'total')
    inlines = [DetalleVentaInline]