from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.core.paginator import Paginator
from django.contrib import messages

from .models import Compra, DetalleCompra
from .forms import CompraForm, DetalleCompraForm
from users.models import UserRole
from inventario.models import Inventario
from inventario.forms import ProductoForm

@login_required
def compras_list(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__compras'))['max_permission'] or 0
    if max_permission == 0: return redirect('dashboard')

    compras = Compra.objects.all()

    # Filtros y Orden
    proveedor_q = request.GET.get('proveedor')
    orden = request.GET.get('orden', '-fecha_compra')

    if proveedor_q:
        compras = compras.filter(proveedor__nombre__icontains=proveedor_q)
    
    if orden == 'antiguas':
        compras = compras.order_by('fecha_compra')
    else:
        compras = compras.order_by('-fecha_compra')

    paginator = Paginator(compras, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'compras/compras_list.html', {
        'page_obj': page_obj, 'max_permission': max_permission
    })


@login_required
def compra_create(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__compras'))['max_permission'] or 0
    if max_permission < 2: return redirect('compras:compras_list')

    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.usuario = request.user
            compra.save()
            return redirect('compras:compra_detalle', pk=compra.pk)
    else:
        form = CompraForm()
    return render(request, 'compras/compra_form.html', {'form': form})


@login_required
def compra_detalle(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__compras'))['max_permission'] or 0
    
    if request.method == 'POST' and max_permission >= 2 and compra.estado == 'PENDIENTE':
        form = DetalleCompraForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.compra = compra
            detalle.save() 
            
            compra.total = sum(d.subtotal for d in compra.detalles.all())
            compra.save()
            messages.success(request, 'Producto agregado al borrador.')
            return redirect('compras:compra_detalle', pk=compra.pk)
    else:
        form = DetalleCompraForm()

    return render(request, 'compras/compra_detalle.html', {'compra': compra, 'form': form, 'max_permission': max_permission})

# --- VISTA: COPIA DE CREAR PRODUCTO PERO DESDE COMPRAS ---
@login_required
def producto_rapido_desde_compra(request, compra_pk):
    compra = get_object_or_404(Compra, pk=compra_pk)

    if request.method == 'POST':
        # TRUCO MAESTRO: Copiamos los datos que llegan y le inyectamos los 0 a la fuerza
        datos = request.POST.copy()
        datos['precio_costo'] = 0
        datos['precio_venta'] = 0
        datos['activo'] = True # Por si tu modelo exige este campo
        
        form = ProductoForm(datos)
        
        if 'categoria' in form.fields:
            form.fields['categoria'].required = False
            
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'¡Producto "{producto.nombre}" creado y listo para usar!')
            return redirect('compras:compra_detalle', pk=compra.pk)
    else:
        form = ProductoForm()
        if 'categoria' in form.fields:
            form.fields['categoria'].required = False

    return render(request, 'compras/producto_crear_agil.html', {'form': form, 'compra': compra})

# --- NUEVAS VISTAS PARA FINALIZAR O CANCELAR ---
@login_required
def compra_finalizar(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST' and compra.estado == 'PENDIENTE':
        with transaction.atomic():
            # Recorremos el detalle y sumamos el stock
            for detalle in compra.detalles.all():
                inv, _ = Inventario.objects.get_or_create(producto=detalle.producto, sucursal=compra.sucursal)
                inv.cantidad += detalle.cantidad
                inv.save()

                if detalle.producto.precio_costo != detalle.precio_costo:
                    detalle.producto.precio_costo = detalle.precio_costo
                    detalle.producto.save()
            
            compra.estado = 'COMPLETADA'
            compra.save()
            messages.success(request, f'Compra #{compra.id} finalizada. Stock ingresado al sistema.')
    return redirect('compras:compras_list')

@login_required
def compra_cancelar(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST' and compra.estado == 'PENDIENTE':
        compra.delete()
        messages.success(request, 'Compra cancelada y eliminada correctamente.')
    return redirect('compras:compras_list')

# Comprobante
@login_required
def compra_comprobante(request, pk):
    return render(request, 'compras/compra_comprobante.html', {'compra': get_object_or_404(Compra, pk=pk)})