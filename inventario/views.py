from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.contrib import messages
import csv

from core.models import Sucursal
from .models import Producto, Inventario
from .forms import ProductoForm
from users.models import UserRole

@login_required
def productos_list(request):
    # Validacion de permisos para el modulo inventario
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__inventario')
    )['max_permission'] or 0

    if max_permission == 0:
        messages.error(request, 'No tienes acceso al módulo de Inventario.')
        return redirect('dashboard')

    productos = Producto.objects.all()

    # Filtros de búsqueda
    codigo = request.GET.get('codigo')
    nombre = request.GET.get('nombre')
    marca = request.GET.get('marca')

    if codigo:
        productos = productos.filter(codigo__icontains=codigo)
    if nombre:
        productos = productos.filter(models.Q(nombre__icontains=nombre) | models.Q(categoria__icontains=nombre))
    if marca:
        productos = productos.filter(marca__icontains=marca)

    # Exportacion a CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventario.csv"'
        response.write('\ufeff'.encode('utf-8'))
        writer = csv.writer(response)

        writer.writerow(['Código', 'Marca', 'Nombre', 'Categoría', 'Precio Costo', 'Precio Venta', 'Stock Total', 'Estado'])

        for prod in productos:
            writer.writerow([
                prod.codigo,
                prod.marca,
                prod.nombre,
                prod.categoria or 'N/A',
                prod.precio_costo,
                prod.precio_venta,
                prod.stock_general,
                'Activo' if prod.activo else 'Inactivo'
            ])
        return response

    # Paginacion
    paginator = Paginator(productos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'max_permission': max_permission,
    }
    return render(request, 'inventario/productos_list.html', context)

# --- CREAR PRODUCTO
@login_required
def producto_create(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__inventario'))['max_permission'] or 0
    if max_permission < 2: return redirect('inventario:productos_list')

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            # Guardamos el stock inicial para cada sucursal
            for suc in Sucursal.objects.all():
                cantidad = request.POST.get(f'stock_{suc.id}')
                if cantidad and cantidad.strip() != '':
                    Inventario.objects.create(producto=producto, sucursal=suc, cantidad=int(cantidad))
            
            messages.success(request, 'Producto y stock inicial creados exitosamente.')
            return redirect('inventario:productos_list')
    else:
        form = ProductoForm()

    # Preparamos la lista de sucursales en 0 para el HTML
    sucursales_data = [{'id': suc.id, 'nombre': suc.nombre, 'cantidad': 0} for suc in Sucursal.objects.all()]

    return render(request, 'inventario/producto_form.html', {'form': form, 'accion': 'Crear', 'sucursales_data': sucursales_data})

# --- EDITAR PRODUCTO
@login_required
def producto_edit(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__inventario'))['max_permission'] or 0
    if max_permission < 2: return redirect('inventario:productos_list')

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            for suc in Sucursal.objects.all():
                cantidad = request.POST.get(f'stock_{suc.id}')
                if cantidad and cantidad.strip() != '':
                    inv, created = Inventario.objects.get_or_create(producto=producto, sucursal=suc)
                    inv.cantidad = int(cantidad)
                    inv.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('inventario:productos_list')
    else:
        form = ProductoForm(instance=producto)

    # Buscamos el stock real que tiene actualmente para mostrarlo en los inputs
    sucursales_data = []
    for suc in Sucursal.objects.all():
        inv = Inventario.objects.filter(producto=producto, sucursal=suc).first()
        sucursales_data.append({'id': suc.id, 'nombre': suc.nombre, 'cantidad': inv.cantidad if inv else 0})

    return render(request, 'inventario/producto_form.html', {'form': form, 'accion': 'Editar', 'producto': producto, 'sucursales_data': sucursales_data})


# --- ACTUALIZAR SOLO STOCK 
@login_required
@login_required
def stock_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__inventario'))['max_permission'] or 0
    if max_permission < 2: return redirect('inventario:productos_list')

    if request.method == 'POST':
        # Actualizar Precios primero
        precio_costo = request.POST.get('precio_costo')
        precio_venta = request.POST.get('precio_venta')
        
        if precio_costo and precio_venta:
            producto.precio_costo = precio_costo
            producto.precio_venta = precio_venta
            producto.save() # Actualiza la fecha_actualizacion

        # Actualizar Stock Fisico
        for suc in Sucursal.objects.all():
            cantidad = request.POST.get(f'stock_{suc.id}')
            if cantidad and cantidad.strip() != '':
                inv, created = Inventario.objects.get_or_create(producto=producto, sucursal=suc)
                inv.cantidad = int(cantidad)
                inv.save()
                
        messages.success(request, f'Stock y precios actualizados para: {producto.nombre}')
        return redirect('inventario:productos_list')

    sucursales_data = []
    for suc in Sucursal.objects.all():
        inv = Inventario.objects.filter(producto=producto, sucursal=suc).first()
        sucursales_data.append({'id': suc.id, 'nombre': suc.nombre, 'cantidad': inv.cantidad if inv else 0})

    return render(request, 'inventario/stock_form.html', {'producto': producto, 'sucursales_data': sucursales_data})

# --- ELIMINAR PRODUCTO
@login_required
def producto_delete(request, pk):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__inventario')
    )['max_permission'] or 0

    if max_permission < 2:
        messages.error(request, 'No tienes permisos para eliminar productos.')
        return redirect('inventario:productos_list')

    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
        
    return redirect('inventario:productos_list')

# --- VER HISTORIA DE PRECIOS DEL PRODUCTO
@login_required
def historial_precios(request, pk):
    # Validamos que el usuario tenga al menos permiso de lectura (1 o más)
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__inventario')
    )['max_permission'] or 0

    if max_permission < 1:
        messages.error(request, 'No tienes permisos para ver el historial de precios.')
        return redirect('inventario:productos_list')

    producto = get_object_or_404(Producto, pk=pk)
    
    # Traemos todo el historial ordenado (el modelo ya lo ordena por -fecha_desde)
    historial = producto.historial_precios.all()

    return render(request, 'inventario/historial_precios.html', {
        'producto': producto,
        'historial': historial,
        'max_permission': max_permission
    })