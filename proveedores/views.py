from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.contrib import messages
import csv

from .models import Proveedor
from .forms import ProveedorForm
from users.models import UserRole

@login_required
def proveedores_list(request):
    # VALIDACIÓN DE PERMISOS
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__proveedores')
    )['max_permission'] or 0

    if max_permission == 0:
        messages.error(request, 'No tienes acceso al módulo de Proveedores.')
        return redirect('dashboard')

    # LÓGICA BASE Y BUSCADOR INTELIGENTE
    proveedores = Proveedor.objects.all()

    criterio = request.GET.get('criterio', 'nombre')
    q = request.GET.get('q', '').strip()
    orden = request.GET.get('orden', 'az')

    # Aplicar filtro inteligente
    if q:
        if criterio == 'nombre':
            proveedores = proveedores.filter(models.Q(nombre__icontains=q) | models.Q(apellido__icontains=q))
        elif criterio == 'documento':
            proveedores = proveedores.filter(numero_documento__icontains=q)
        elif criterio == 'rubro':
            proveedores = proveedores.filter(rubro__icontains=q)
        elif criterio == 'ubicacion':
            proveedores = proveedores.filter(models.Q(provincia__icontains=q) | models.Q(localidad__icontains=q))

    # Aplicar ordenamiento
    orden_opciones = {
        'az': ['nombre', 'apellido'],
        'za': ['-nombre', '-apellido'],
        'recientes': ['-fecha_registro'],
        'antiguos': ['fecha_registro'],
    }
    orden_db = orden_opciones.get(orden, ['nombre', 'apellido'])
    proveedores = proveedores.order_by(*orden_db)

    # EXPORTACIÓN A CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="proveedores.csv"'
        response.write('\ufeff'.encode('utf-8'))
        writer = csv.writer(response)

        writer.writerow([
            'Nombre', 'Apellido', 'Rubro', 'Tipo Doc', 'Documento', 
            'CBU/Alias', 'Provincia', 'Localidad', 
            'Teléfono', 'Email', 'Fecha Alta'
        ])

        for prov in proveedores:
            writer.writerow([
                prov.nombre,
                prov.apellido or '',
                prov.rubro,
                prov.tipo_documento,
                prov.numero_documento,
                prov.cbu_alias or 'N/A',
                prov.provincia,
                prov.localidad,
                prov.telefono or 'N/A',
                prov.email or 'N/A',
                prov.fecha_registro.strftime('%d/%m/%Y'),
            ])
        return response

    # PAGINACIÓN Y CONTEXTO
    paginator = Paginator(proveedores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'max_permission': max_permission,
        
        # Devolvemos esto para que la barra de búsqueda se mantenga al recargar
        'criterio_actual': criterio,
        'q_actual': q,
        'orden_actual': orden,
    }

    return render(request, 'proveedores/proveedores_list.html', context)


@login_required
def proveedor_create(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__proveedores')
    )['max_permission'] or 0

    if max_permission < 2:
        messages.error(request, 'No tienes permisos para crear proveedores.')
        return redirect('proveedores:proveedores_list')

    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor creado exitosamente.')
            return redirect('proveedores:proveedores_list')
    else:
        form = ProveedorForm()

    return render(request, 'proveedores/proveedor_form.html', {'form': form, 'accion': 'Crear'})


@login_required
def proveedor_edit(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__proveedores')
    )['max_permission'] or 0

    if max_permission < 2:
        messages.error(request, 'No tienes permisos para editar proveedores.')
        return redirect('proveedores:proveedores_list')

    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado exitosamente.')
            return redirect('proveedores:proveedores_list')
    else:
        form = ProveedorForm(instance=proveedor)

    context = {
        'form': form,
        'proveedor': proveedor,
        'accion': 'Editar',
    }

    return render(request, 'proveedores/proveedor_form.html', context)


@login_required
def proveedor_delete(request, pk):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__proveedores')
    )['max_permission'] or 0

    if max_permission < 2:
        messages.error(request, 'No tienes permisos para eliminar proveedores.')
        return redirect('proveedores:proveedores_list')

    proveedor = get_object_or_404(Proveedor, pk=pk)

    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, 'Proveedor eliminado exitosamente.')
        return redirect('proveedores:proveedores_list')

    return redirect('proveedores:proveedores_list')