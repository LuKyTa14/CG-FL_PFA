from django.db import models
from django.contrib.auth import get_user_model
from clientes.models import Cliente
from inventario.models import Producto
from core.models import Sucursal
from decimal import Decimal

User = get_user_model()

class Venta(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'En Curso (Carrito)'),
        ('COMPLETADA', 'Cobrada y Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    # Los métodos de pago ahora viven acá para que PagoVenta los consuma
    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('DEBITO', 'Tarjeta Débito'),
        ('CREDITO', 'Tarjeta Crédito'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('BILLETERA_VIRTUAL', 'Billetera Virtual / QR'), # Renombrado
        ('CUENTA_CORRIENTE', 'Cuenta Corriente'),
        ('OTROS', 'Otros'), # Agregado
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='compras_realizadas')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='ventas')
    cajero = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    fecha_venta = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    
    # NUEVO: Campo para descuento global del ticket
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'ventas'
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha_venta']

    def __str__(self):
        cliente_nombre = f"{self.cliente.nombre} {self.cliente.apellido}" if self.cliente else "Consumidor Final"
        return f"Venta #{self.id} - {cliente_nombre} (${self.total})"


# NUEVA TABLA: Para permitir pagos combinados
class PagoVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='pagos')
    metodo_pago = models.CharField(max_length=20, choices=Venta.METODO_PAGO_CHOICES)
    monto = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'ventas_pagos'
        verbose_name = 'Pago de Venta'
        verbose_name_plural = 'Pagos de Venta'

    def __str__(self):
        return f"{self.get_metodo_pago_display()} - ${self.monto} (Venta #{self.venta.id})"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'ventas_detalles'
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Venta #{self.venta.id})"