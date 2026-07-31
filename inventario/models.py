from django.db import models
from core.models import Sucursal
from django.utils import timezone

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
    
    def save(self, *args, **kwargs): #FUNCION PARA GUARDAR HISTORIAL DE PRECIOS
        is_new = self.pk is None
        precio_venta_cambio = False

        if not is_new:
            # Nos fijamos si cambio el precio de venta
            prod_viejo = Producto.objects.get(pk=self.pk)
            if prod_viejo.precio_venta != self.precio_venta:
                precio_venta_cambio = True

        super().save(*args, **kwargs)

        # Si es nuevo o el precio de venta cambio, guardamos historial
        if is_new or precio_venta_cambio:
            ultimo_historial = self.historial_precios.filter(fecha_hasta__isnull=True).first()
            if ultimo_historial:
                ultimo_historial.fecha_hasta = timezone.now()
                ultimo_historial.save()

            HistorialPrecio.objects.create(
                producto=self,
                precio_venta=self.precio_venta
            )


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


class HistorialPrecio(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='historial_precios')
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2)
    
    fecha_desde = models.DateTimeField(auto_now_add=True)
    fecha_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'historial_precios'
        ordering = ['-fecha_desde']

    def __str__(self):
        return f"{self.producto.nombre} - ${self.precio_venta} desde {self.fecha_desde.strftime('%d/%m/%Y')}"