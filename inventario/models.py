from django.db import models
from core.models import Sucursal

# Productos por Sucursales
class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    marca = models.CharField(max_length=100)
    nombre = models.CharField(max_length=150)
    categoria = models.CharField(max_length=100, blank=True, null=True)

    # DecimalField --> es mejor para manejar dinero y no perder centavos
    precio_costo = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    activo = models.BooleanField(default=True)
    
    @property
    def stock_general(self):
        # Suma las cantidades de todos los inventarios (sucursales) de este producto
        total = self.inventarios.aggregate(total=models.Sum('cantidad'))['total']
        return total or 0

    @property
    def estado_stock(self):
        if self.stock_general > 0:
            return "Disponible"
        return "Sin Stock"

    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.marca} {self.nombre}"



# Intersección entre Productos y Sucursales
class Inventario(models.Model):
    # Relacion Producto y Sucursal
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='inventarios')
    
    # El stock real en esa sucursal
    cantidad = models.IntegerField(default=0)
    
    # stock_minimo = models.IntegerField(default=5, help_text="Aviso de poco stock en esta sucursal")
    
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventario_sucursales'
        verbose_name = 'Inventario por Sucursal'
        verbose_name_plural = 'Inventarios por Sucursales'
        # No puede haber dos registros del mismo producto en la misma sucursal
        unique_together = ('producto', 'sucursal') 

    def __str__(self):
        return f"{self.producto.nombre} en {self.sucursal.nombre}: {self.cantidad} unidades"