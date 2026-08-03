from django.db import models
from django.contrib.auth import get_user_model
from clientes.models import Cliente
from inventario.models import Producto
from core.models import Sucursal

User = get_user_model()

class Venta(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'En Curso (Carrito)'),
        ('COMPLETADA', 'Cobrada y Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('DEBITO', 'Tarjeta Débito'),
        ('CREDITO', 'Tarjeta Crédito'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('MERCADO_PAGO_QR', 'Mercado Pago / QR'),
        ('CUENTA_CORRIENTE', 'Cuenta Corriente'),
    ]

    # Si el cliente es Null, se asume "Consumidor Final"
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='compras_realizadas')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='ventas')
    cajero = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    fecha_venta = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='EFECTIVO')
    
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


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    
    cantidad = models.IntegerField(default=1)
    # Guardamos el precio al que se vendio hoy. Si mañana aumenta, esta factura no se altera.
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