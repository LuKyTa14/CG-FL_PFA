from django.contrib import admin
from .models import Producto, Inventario

# Permite editar el stock por sucursal dentro de la vista del producto
class InventarioInline(admin.TabularInline):
    model = Inventario
    extra = 1           #fila vacia para agregar stock

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # 'stock_general' aunque no es una columna real --> se puede mostrar/editar
    list_display = ('codigo', 'marca', 'nombre', 'categoria', 'precio_costo', 'precio_venta', 'stock_general', 'activo')
    search_fields = ('codigo', 'nombre', 'marca', 'categoria')
    list_filter = ('categoria', 'marca', 'activo')
    
    # Tabla de sucursales adentro del producto
    inlines = [InventarioInline]

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'sucursal', 'cantidad')
    list_filter = ('sucursal',)
    search_fields = ('producto__nombre', 'producto__codigo')