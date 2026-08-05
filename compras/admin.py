from django.contrib import admin
from .models import Compra, DetalleCompra

class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'proveedor', 'sucursal', 'usuario', 'fecha_compra', 'estado', 'total')
    list_filter = ('estado', 'sucursal', 'fecha_compra')
    search_fields = ('id', 'proveedor__nombre')
    readonly_fields = ('fecha_compra', 'total')
    inlines = [DetalleCompraInline]
    date_hierarchy = 'fecha_compra'