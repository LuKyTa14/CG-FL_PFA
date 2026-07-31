from django.contrib import admin
from .models import Producto, Inventario, HistorialPrecio

# --- TABLAS INCRUSTADAS (INLINES) ---

# Permite editar el stock por sucursal dentro de la vista del producto
class InventarioInline(admin.TabularInline):
    model = Inventario
    extra = 1

# Permite ver el historial de precios dentro de la vista del producto
class HistorialPrecioInline(admin.TabularInline):
    model = HistorialPrecio
    extra = 0
    # Lo hacemos de solo lectura para no corromper el historial a mano
    readonly_fields = ('precio_venta', 'fecha_desde', 'fecha_hasta')
    
    def has_add_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

# --- REGISTROS PRINCIPALES ---

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'marca', 'nombre', 'categoria', 'precio_costo', 'precio_venta', 'stock_general', 'activo')
    search_fields = ('codigo', 'nombre', 'marca', 'categoria')
    list_filter = ('categoria', 'marca', 'activo')
    
    # ¡Aquí le decimos que muestre ambas tablas al fondo!
    inlines = [InventarioInline, HistorialPrecioInline]


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'sucursal', 'cantidad')
    list_filter = ('sucursal',)
    search_fields = ('producto__nombre', 'producto__codigo')


@admin.register(HistorialPrecio)
class HistorialPrecioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'precio_venta', 'fecha_desde', 'fecha_hasta')
    list_filter = ('fecha_desde', 'fecha_hasta', 'producto')
    search_fields = ('producto__nombre', 'producto__codigo', 'producto__marca')
    readonly_fields = ('fecha_desde',)