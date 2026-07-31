from django.contrib import admin
from .models import Compra, DetalleCompra

class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 1

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'proveedor', 'sucursal', 'fecha_compra', 'total', 'usuario')
    list_filter = ('sucursal', 'proveedor', 'fecha_compra')
    search_fields = ('proveedor__nombre', 'observaciones')
    readonly_fields = ('fecha_compra', 'total')
    inlines = [DetalleCompraInline]