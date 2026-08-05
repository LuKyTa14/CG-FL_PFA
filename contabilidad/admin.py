from django.contrib import admin
from .models import CierreCaja

@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display = ('id', 'sucursal', 'usuario', 'fecha_cierre', 'total_recaudado', 'mostrar_diferencia')
    list_filter = ('sucursal', 'fecha_cierre', 'usuario')
    search_fields = ('sucursal__nombre', 'usuario__username', 'observaciones')
    readonly_fields = ('fecha_cierre', 'total_recaudado', 'mostrar_diferencia')
    date_hierarchy = 'fecha_cierre'

    fieldsets = (
        ('Información General', {
            'fields': ('sucursal', 'usuario', 'fecha_inicio', 'fecha_cierre')
        }),
        ('Ingresos del Sistema', {
            'fields': (
                'total_efectivo', 'total_tarjeta_debito', 'total_tarjeta_credito',
                'total_transferencia', 'total_billetera_virtual', 'total_otros', 
                'total_recaudado'
            )
        }),
        ('Control Físico (Arqueo)', {
            'fields': ('efectivo_usado', 'efectivo_declarado', 'mostrar_diferencia', 'observaciones')
        }),
    )

    # Creamos esta funcion para poder mostrar la property en el admin
    def mostrar_diferencia(self, obj):
        return obj.diferencia_efectivo
    mostrar_diferencia.short_description = 'Diferencia Física'