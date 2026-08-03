from django.contrib import admin
from .models import Cliente, MovimientoCuentaCorriente

# BONUS: Esto incrusta el historial de pagos dentro de la ficha del cliente en el admin
class MovimientoCuentaCorrienteInline(admin.TabularInline):
    model = MovimientoCuentaCorriente
    extra = 0 # No mostrar filas vacías extra
    readonly_fields = ('fecha', 'tipo', 'monto', 'descripcion', 'cajero')
    can_delete = False # Evita que un administrador borre un pago "sin querer"

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    # Agregamos el saldo_cuenta_corriente al final de la lista
    list_display = ('nombre', 'apellido', 'tipo_documento', 'numero_documento', 'localidad', 'saldo_cuenta_corriente')
    search_fields = ('nombre', 'apellido', 'numero_documento')
    list_filter = ('provincia', 'tipo_documento', 'fecha_registro')
    
    # Agregamos la tablita incrustada
    inlines = [MovimientoCuentaCorrienteInline]

# Registramos el historial de movimientos de manera independiente por si hay que auditarlos todos juntos
@admin.register(MovimientoCuentaCorriente)
class MovimientoCuentaCorrienteAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'cliente', 'tipo', 'monto', 'cajero')
    list_filter = ('tipo', 'fecha', 'cajero')
    search_fields = ('cliente__nombre', 'cliente__apellido', 'cliente__numero_documento', 'descripcion')
    readonly_fields = ('fecha',) # La fecha se pone sola, no se edita
    
    # Ordenamos del más nuevo al más viejo
    ordering = ('-fecha',)