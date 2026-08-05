from django.db import models
from django.contrib.auth import get_user_model
from core.models import Sucursal

User = get_user_model()

class CierreCaja(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='cierres_caja')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, help_text="Usuario que realizó el cierre")
    
    fecha_inicio = models.DateTimeField(help_text="Fecha y hora del último cierre anterior")
    fecha_cierre = models.DateTimeField(auto_now_add=True)

    # TOTALES DEL SISTEMA (Ingresos)
    total_efectivo = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_tarjeta_debito = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) 
    total_tarjeta_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) 
    total_transferencia = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_billetera_virtual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_otros = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Gran Total calculado y guardado en BD
    total_recaudado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)


    # CONTROL FÍSICO (Egresos y Arqueo)
    efectivo_usado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)      # gastos del dia en efectivo sacado de la caja
    efectivo_declarado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # efectivo al cierre de caja 
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'cierre_caja'
        verbose_name = 'Cierre de Caja'
        verbose_name_plural = 'Cierres de Caja'
        ordering = ['-fecha_cierre']

    def __str__(self):
        return f"Cierre en {self.sucursal.nombre} - {self.fecha_cierre.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Calculamos el total exacto justo antes de que se guarde en la base de datos
        self.total_recaudado = (
            self.total_efectivo + 
            self.total_tarjeta_debito + 
            self.total_tarjeta_credito + 
            self.total_transferencia + 
            self.total_billetera_virtual +
            self.total_otros
        )
        super().save(*args, **kwargs)
    
    @property
    def diferencia_efectivo(self):
        efectivo_esperado = self.total_efectivo - self.efectivo_usado
        # Si da Negativo = Faltante. Si da Positivo = Sobrante.
        return self.efectivo_declarado - efectivo_esperado