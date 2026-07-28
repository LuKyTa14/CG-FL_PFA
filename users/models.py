from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # user_id, username, password y el validar de no repetir usuario (is_active).
    # AbstractUser se encarga de todo eso de forma segura.

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Role(models.Model):
    PERMISSION_CHOICE = [
        (0, 'No acceso'),
        (1, 'Ver solamente'),
        (2, 'Crear y Modificar')
    ]

    role_name = models.CharField(max_length=50, primary_key=True)
    proveedores = models.IntegerField(choices=PERMISSION_CHOICE, default=0)
    compras = models.IntegerField(choices=PERMISSION_CHOICE, default=0)
    clientes = models.IntegerField(choices=PERMISSION_CHOICE, default=0)
    ventas = models.IntegerField(choices=PERMISSION_CHOICE, default=0)
    inventario = models.IntegerField(choices=PERMISSION_CHOICE, default=0)
    contabilidad = models.IntegerField(choices=PERMISSION_CHOICE, default=0)
    reportes = models.IntegerField(choices=PERMISSION_CHOICE, default=0)
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.role_name
    

class UserRole(models.Model):
    # Corregido: ForeignKey en lugar de ForeingKey
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        db_table = 'user_roles'
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
        unique_together = ('user_id', 'role')

    def __str__(self):
        return f"{self.user_id.username} - {self.role.role_name}"
