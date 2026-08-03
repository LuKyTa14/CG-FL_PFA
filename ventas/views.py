from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.core.paginator import Paginator
from django.contrib import messages

from .models import Venta, DetalleVenta
from users.models import UserRole
from inventario.models import Producto, Inventario
from clientes.models import MovimientoCuentaCorriente, Cliente
from core.models import Sucursal

@login_required
def ventas_list(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__ventas'))['max_permission'] or 0
    if max_permission == 0: return redirect('dashboard')

    # MAGIA: Excluimos las ventas canceladas. Solo se verán en el panel de administrador.
    ventas = Venta.objects.exclude(estado='CANCELADA')

    ticket_q = request.GET.get('ticket')
    cliente_q = request.GET.get('cliente')
    orden = request.GET.get('orden', '-fecha_venta')

    if ticket_q and ticket_q.isdigit():
        ventas = ventas.filter(id=ticket_q)
        
    if cliente_q:
        ventas = ventas.filter(
            models.Q(cliente__nombre__icontains=cliente_q) | 
            models.Q(cliente__apellido__icontains=cliente_q)
        )
        
    if orden == 'antiguas':
        ventas = ventas.order_by('fecha_venta')
    else:
        ventas = ventas.order_by('-fecha_venta')

    paginator = Paginator(ventas, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'ventas/ventas_list.html', {
        'page_obj': page_obj, 'max_permission': max_permission
    })

# --- CREAR VENTA
@login_required
def venta_create(request):
    # En vez de pedir datos en otra pantalla, creamos el "carrito" al instante
    sucursal_default = Sucursal.objects.first()
    venta = Venta.objects.create(sucursal=sucursal_default, cajero=request.user, estado='PENDIENTE')
    return redirect('ventas:venta_detalle', pk=venta.pk)

# --- DETALLE VENTA
@login_required
def venta_detalle(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    
    if request.method == 'POST' and venta.estado == 'PENDIENTE':
        # 1. Guardamos la cabecera (se actualiza automáticamente en cada clic)
        venta.cliente_id = request.POST.get('cliente') or None
        venta.sucursal_id = request.POST.get('sucursal') or venta.sucursal_id
        venta.metodo_pago = request.POST.get('metodo_pago', 'EFECTIVO')
        venta.save()

        # 2. Lógica de los botones de Acción
        if 'add_producto' in request.POST:
            producto_id = request.POST.get('producto_id')
            cantidad = int(request.POST.get('cantidad', 1))
            if producto_id:
                producto = get_object_or_404(Producto, pk=producto_id)
                # BONUS: Si ya existe en el ticket, le suma la cantidad; si no, lo crea.
                detalle, created = DetalleVenta.objects.get_or_create(
                    venta=venta, producto=producto,
                    defaults={'cantidad': cantidad, 'precio_unitario': producto.precio_venta}
                )
                if not created:
                    detalle.cantidad += cantidad
                    detalle.save()
                    
        elif 'delete_item' in request.POST:
            # Eliminar el producto entero del ticket
            detalle = get_object_or_404(DetalleVenta, pk=request.POST.get('delete_item'), venta=venta)
            detalle.delete()
            
        elif 'sumar_item' in request.POST:
            # Sumar 1 a la cantidad
            detalle = get_object_or_404(DetalleVenta, pk=request.POST.get('sumar_item'), venta=venta)
            detalle.cantidad += 1
            detalle.save()
            
        elif 'restar_item' in request.POST:
            # Restar 1 a la cantidad (Si llega a 0, se elimina)
            detalle = get_object_or_404(DetalleVenta, pk=request.POST.get('restar_item'), venta=venta)
            if detalle.cantidad > 1:
                detalle.cantidad -= 1
                detalle.save()
            else:
                detalle.delete()

        # 3. Recalculamos el Total de la venta siempre al final
        venta.total = sum(d.subtotal for d in venta.detalles.all())
        venta.save()
        
        return redirect('ventas:venta_detalle', pk=venta.pk)

    context = {
        'venta': venta,
        'clientes': Cliente.objects.all(),
        'sucursales': Sucursal.objects.all(),
        'productos': Producto.objects.filter(activo=True),
        'metodos_pago': Venta.METODO_PAGO_CHOICES
    }
    return render(request, 'ventas/venta_detalle.html', context)

# --- FINALIZAR VENTA
@login_required
def venta_finalizar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST' and venta.estado == 'PENDIENTE':
        with transaction.atomic():
            # Guardado final de la cabecera por si cambió algo a último segundo
            venta.cliente_id = request.POST.get('cliente') or None
            venta.sucursal_id = request.POST.get('sucursal') or venta.sucursal_id
            venta.metodo_pago = request.POST.get('metodo_pago', 'EFECTIVO')

            # Descontar stock
            for detalle in venta.detalles.all():
                inv, _ = Inventario.objects.get_or_create(producto=detalle.producto, sucursal=venta.sucursal)
                inv.cantidad -= detalle.cantidad
                inv.save()
            
            venta.estado = 'COMPLETADA'
            venta.save()
            messages.success(request, f'¡Venta cobrada! Total: ${venta.total}')
    return redirect('ventas:ventas_list')

@login_required
def venta_finalizar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    
    if request.method == 'POST' and venta.estado == 'PENDIENTE':
        
        # 1. Capturamos lo que eligió el cajero en los desplegables
        cliente_id = request.POST.get('cliente')
        metodo_pago = request.POST.get('metodo_pago', 'EFECTIVO')
        sucursal_id = request.POST.get('sucursal')
        
        # --- VALIDACIÓN DE SEGURIDAD ---
        # Si quiere fiar, sí o sí tiene que haber elegido un cliente
        if metodo_pago == 'CUENTA_CORRIENTE' and not cliente_id:
            messages.error(request, '⚠️ ERROR: No puedes cobrar con Cuenta Corriente a un "Consumidor Final". Debes seleccionar un cliente.')
            return redirect('ventas:venta_detalle', pk=venta.pk)

        with transaction.atomic():
            # 2. Guardamos los datos finales en la venta
            venta.metodo_pago = metodo_pago
            if cliente_id:
                venta.cliente_id = cliente_id
            if sucursal_id:
                venta.sucursal_id = sucursal_id

            # --- LA MAGIA: IMPACTAR EN CUENTA CORRIENTE ---
            if metodo_pago == 'CUENTA_CORRIENTE':
                cliente = venta.cliente
                # Le sumamos el total del ticket a lo que ya debía
                cliente.saldo_cuenta_corriente += venta.total
                cliente.save()
                
                # ¡CORRECCIÓN AQUÍ! Usamos formato de Python puro (:05d)
                MovimientoCuentaCorriente.objects.create(
                    cliente=cliente,
                    tipo='DEUDA',
                    monto=venta.total,
                    descripcion=f'Venta a crédito (Ticket #{venta.id:05d})',
                    cajero=request.user
                )

            # 4. Cerramos el ticket
            venta.estado = 'COMPLETADA'
            venta.save()
            messages.success(request, f'¡Venta cobrada con éxito! (${venta.total})')
            
    return redirect('ventas:ventas_list')

# --- CANCELAR VENTA
@login_required
def venta_cancelar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if venta.estado == 'PENDIENTE':
        venta.estado = 'CANCELADA' # En lugar de eliminar, cambiamos el estado para no perder el salto de ID
        venta.save()
        messages.success(request, f'El Ticket #{venta.id} ha sido anulado y guardado en el historial.')
    return redirect('ventas:ventas_list')

# --- COMPROBANTE VENTA
@login_required
def venta_comprobante(request, pk):
    return render(request, 'ventas/venta_comprobante.html', {'venta': get_object_or_404(Venta, pk=pk)})