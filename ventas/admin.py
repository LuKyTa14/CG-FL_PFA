from django.contrib import admin
from .models import Venta, DetalleVenta, PagoVenta

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ('subtotal',)

class PagoVentaInline(admin.TabularInline):
    model = PagoVenta
    extra = 0

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'sucursal', 'cajero', 'fecha_venta', 'estado', 'total')
    list_filter = ('estado', 'sucursal', 'fecha_venta')
    search_fields = ('id', 'cliente__nombre', 'cliente__apellido')
    readonly_fields = ('fecha_venta', 'total')
    inlines = [DetalleVentaInline, PagoVentaInline] # Muestra el detalle y los pagos adentro
    date_hierarchy = 'fecha_venta'

@admin.register(PagoVenta)
class PagoVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'venta', 'metodo_pago', 'monto')
    list_filter = ('metodo_pago',)