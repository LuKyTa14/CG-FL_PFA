from django.db import models

class Cliente(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('DNI', 'DNI'),
        ('CUIL', 'CUIL'),
        ('CUIT', 'CUIT'),
        ('PASAPORTE', 'PASAPORTE'),
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES, default='DNI')
    # unique=True --> para no cargar dos veces al mismo cliente
    numero_documento = models.CharField(max_length=50, unique=True) 
    provincia = models.CharField(max_length=100)
    localidad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    
    # Campos Opcionales (blank=True --> permite que el formulario HTML pase vacio)
    barrio = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=20)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Guardamos fecha de regristro 
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre', 'apellido'] # Ordena por nombre

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.numero_documento})"