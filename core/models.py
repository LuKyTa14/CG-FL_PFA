from django.db import models

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100, help_text="Ej: Casa Central, Sucursal Norte")
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    
    # Sucursal por defecto (autoasignar stock), si es que no tiene sucursales
    es_principal = models.BooleanField(default=False) 

    class Meta:
        db_table = 'sucursales'
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'

    def __str__(self):
        return self.nombre