from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.contrib import messages
import csv
from django.db import transaction
from decimal import Decimal
from django.db.models import Sum, Q

from .models import Cliente, MovimientoCuentaCorriente
from .forms import ClienteForm
from users.models import UserRole
from clientes.models import MovimientoCuentaCorriente, Cliente
from core.models import Sucursal
from ventas.models import Venta

# --- LISTAR CLIENTE
@login_required
def clientes_list(request):

    # VALIDACIÓN DE PERMISOS
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__clientes')
    )['max_permission'] or 0

    if max_permission == 0:
        messages.error(request, 'No tienes acceso al módulo de Clientes.')
        return redirect('dashboard')


    # LÓGICA BASE Y BUSCADOR INTELIGENTE
    clientes = Cliente.objects.all()

    criterio = request.GET.get('criterio', 'nombre')
    q = request.GET.get('q', '').strip()
    orden = request.GET.get('orden', 'az')

    # Aplicar filtro inteligente
    if q:
        if criterio == 'nombre':
            # Busca en nombre O apellido
            clientes = clientes.filter(models.Q(nombre__icontains=q) | models.Q(apellido__icontains=q))
        elif criterio == 'documento':
            clientes = clientes.filter(numero_documento__icontains=q)
        elif criterio == 'ubicacion':
            # Busca en provincia O localidad
            clientes = clientes.filter(models.Q(provincia__icontains=q) | models.Q(localidad__icontains=q))

    # Aplicar ordenamiento
    orden_opciones = {
        'az': ['apellido', 'nombre'],      # Ordena por apellido, y si hay empate, por nombre
        'za': ['-apellido', '-nombre'],
        'recientes': ['-fecha_registro'],  # Los últimos que agregaste al sistema
        'antiguos': ['fecha_registro'],
    }
    # Si pasa algo raro, por defecto ordena de la A a la Z
    orden_db = orden_opciones.get(orden, ['apellido', 'nombre'])
    clientes = clientes.order_by(*orden_db)


    # EXPORTACIÓN A CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clientes.csv"'
        response.write('\ufeff'.encode('utf-8'))
        writer = csv.writer(response)

        writer.writerow([
            'Nombre', 'Apellido', 'Tipo Doc', 'Documento', 
            'Provincia', 'Localidad', 'Dirección', 'Barrio', 
            'CP', 'Teléfono', 'Email', 'Fecha Alta'
        ])

        for cliente in clientes:
            writer.writerow([
                cliente.nombre,
                cliente.apellido,
                cliente.tipo_documento,
                cliente.numero_documento,
                cliente.provincia,
                cliente.localidad,
                cliente.direccion,
                cliente.barrio or 'N/A',
                cliente.codigo_postal,
                cliente.telefono or 'N/A',
                cliente.email or 'N/A',
                cliente.fecha_registro.strftime('%d/%m/%Y %H:%M'),
            ])
        return response

    # PAGINACIÓN Y CONTEXTO
    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'max_permission': max_permission,
        
        # Devolvemos esto para que la barra de búsqueda se mantenga
        'criterio_actual': criterio,
        'q_actual': q,
        'orden_actual': orden,
    }

    return render(request, 'clientes/clientes_list.html', context)


# --- CREAR CLIENTE
@login_required
def cliente_create(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__clientes')
    )['max_permission'] or 0

    if max_permission < 2:
        messages.error(request, 'No tienes permisos para crear clientes.')
        return redirect('clientes:clientes_list')

    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('clientes:clientes_list')
    else:
        form = ClienteForm()

    return render(request, 'clientes/cliente_form.html', {'form': form, 'accion': 'Crear'})

# --- EDITAR CLIENTE
@login_required
def cliente_edit(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__clientes')
    )['max_permission'] or 0

    if max_permission < 2:
        messages.error(request, 'No tienes permisos para editar clientes.')
        return redirect('clientes:clientes_list')

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('clientes:clientes_list')
    else:
        form = ClienteForm(instance=cliente)

    context = {
        'form': form,
        'cliente': cliente,
        'accion': 'Editar',
    }

    return render(request, 'clientes/cliente_form.html', context)

# --- ELIMINAR CLIENTE
@login_required
def cliente_delete(request, pk):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__clientes')
    )['max_permission'] or 0

    if max_permission < 2:
        messages.error(request, 'No tienes permisos para eliminar clientes.')
        return redirect('clientes:clientes_list')

    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect('clientes:clientes_list')

    return redirect('clientes:clientes_list')

# --- LOGICA DE MANEJO DE CUENTAS CORRIENTES
def cuenta_corriente_list(request):
    # TARJETA DE RESUMEN
    total_credito = Cliente.objects.filter(saldo_cuenta_corriente__gt=0).aggregate(
        total=Sum('saldo_cuenta_corriente')
    )['total'] or 0

    # LÓGICA BASE Y BUSCADOR INTELIGENTE
    clientes = Cliente.objects.all()

    criterio = request.GET.get('criterio', 'nombre')
    q = request.GET.get('q', '').strip()
    orden = request.GET.get('orden', 'az')

    # Aplicar filtro inteligente
    if q:
        if criterio == 'nombre':
            clientes = clientes.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q))
        elif criterio == 'documento':
            clientes = clientes.filter(numero_documento__icontains=q)

    # Aplicar ordenamiento
    orden_opciones = {
        'az': ['apellido', 'nombre'],
        'za': ['-apellido', '-nombre'],
        'mayor_deuda': ['-saldo_cuenta_corriente'], # El signo menos ordena de mayor a menor
        'menor_deuda': ['saldo_cuenta_corriente'],
    }
    orden_db = orden_opciones.get(orden, ['apellido', 'nombre'])
    clientes = clientes.order_by(*orden_db)

    # EXPORTACIÓN A CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="cuentas_corrientes.csv"'
        response.write('\ufeff'.encode('utf-8')) # Soporte para tildes y ñ en Excel
        writer = csv.writer(response)

        writer.writerow(['Documento', 'Apellido', 'Nombre', 'Teléfono', 'Email', 'Saldo Actual'])

        for cliente in clientes:
            writer.writerow([
                cliente.numero_documento or '-',
                cliente.apellido,
                cliente.nombre or '',
                cliente.telefono or 'N/A',
                cliente.email or 'N/A',
                cliente.saldo_cuenta_corriente,
            ])
        return response

    # PAGINACIÓN Y CONTEXTO
    paginator = Paginator(clientes, 15) # Mantengo tus 15 por página
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_obj': page_obj,
        'total_credito': total_credito,
        # Variables para mantener el estado del buscador
        'criterio_actual': criterio,
        'q_actual': q,
        'orden_actual': orden,
    }
    
    return render(request, 'clientes/cuenta_corriente_list.html', context)

# --- DETALLE CUENTAS CORRIENTES
@login_required
def cuenta_corriente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    movimientos = cliente.movimientos.all().order_by('-fecha')
    
    # 1. Traemos las sucursales de la BD
    sucursales = Sucursal.objects.all()
    
    # 2. Traemos los métodos de pago, pero FILTRAMOS "Cuenta Corriente" (no se puede pagar deuda con deuda)
    metodos_pago = [m for m in Venta.METODO_PAGO_CHOICES if m[0] != 'CUENTA_CORRIENTE']
    
    if request.method == 'POST':
        monto_str = request.POST.get('monto', '0')
        metodo_pago_key = request.POST.get('metodo_pago', 'EFECTIVO')
        sucursal_id = request.POST.get('sucursal')
        nota = request.POST.get('descripcion', '')
        
        try:
            monto = Decimal(monto_str)
            if monto > 0:
                with transaction.atomic():
                    # 3. Traducimos el ID de la Sucursal a su Nombre real
                    sucursal_obj = Sucursal.objects.filter(pk=sucursal_id).first()
                    nombre_sucursal = sucursal_obj.nombre if sucursal_obj else "Sede Central"
                    
                    # 4. Traducimos la key del método ('EFECTIVO') a su nombre legible ('Efectivo')
                    diccionario_metodos = dict(Venta.METODO_PAGO_CHOICES)
                    nombre_metodo = diccionario_metodos.get(metodo_pago_key, metodo_pago_key)

                    # Armamos la descripción perfecta para el historial
                    descripcion_completa = f"Pago en {nombre_metodo} ({nombre_sucursal})"
                    if nota:
                        descripcion_completa += f" | {nota}"

                    MovimientoCuentaCorriente.objects.create(
                        cliente=cliente,
                        tipo='PAGO',
                        monto=monto,
                        descripcion=descripcion_completa,
                        cajero=request.user,
                        sucursal_id=sucursal_id,
                        metodo_pago=metodo_pago_key 
                    )
                    
                    cliente.saldo_cuenta_corriente -= monto
                    cliente.save()
                    
                    messages.success(request, f'Se registró el pago de ${monto} correctamente.')
            else:
                messages.error(request, 'El monto debe ser mayor a cero.')
        except:
            messages.error(request, 'Monto inválido. Revisa los datos ingresados.')
            
        return redirect('clientes:cuenta_corriente_detalle', pk=cliente.pk)
        
    return render(request, 'clientes/cuenta_corriente_detalle.html', {
        'cliente': cliente,
        'movimientos': movimientos,
        'sucursales': sucursales,
        'metodos_pago': metodos_pago
    })