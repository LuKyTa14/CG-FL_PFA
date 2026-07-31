from django.db import models
from django.contrib.auth import get_user_model
from proveedores.models import Proveedor
from inventario.models import Producto
from core.models import Sucursal

User = get_user_model()

class Compra(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Borrador (Sin ingresar)'),
        ('COMPLETADA', 'Completada (Stock Sumado)'),
    ]

    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    fecha_compra = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'compras'
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-fecha_compra']

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor.nombre}"


class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    
    cantidad = models.IntegerField(default=1)
    precio_costo = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'compras_detalles'

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_costo
        super().save(*args, **kwargs)