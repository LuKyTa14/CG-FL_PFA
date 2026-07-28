from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, UserRole

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Qué columnas se ven en la tabla
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    # Filtros laterales
    list_filter = ('is_staff', 'is_active', 'date_joined')
    # Barra de búsqueda
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    # Aquí ponemos todos tus módulos exactamente como se llaman en models.py
    list_display = ('role_name', 'proveedores', 'compras', 'clientes', 'ventas', 'inventario', 'contabilidad', 'reportes')
    list_filter = ('proveedores', 'compras', 'clientes', 'ventas', 'inventario', 'contabilidad', 'reportes')
    search_fields = ('role_name',)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'role')
    list_filter = ('role',)
    # Como user_id y role son ForeignKeys, usamos doble guion bajo (__) 
    search_fields = ('user_id__username', 'role__role_name')