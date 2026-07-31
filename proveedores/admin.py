from django.contrib import admin
from .models import Proveedor

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'tipo_documento', 'numero_documento', 'rubro', 'telefono', 'email')
    search_fields = ('nombre', 'apellido', 'numero_documento', 'rubro')
    list_filter = ('tipo_documento', 'rubro', 'provincia')
    ordering = ('nombre', 'apellido')