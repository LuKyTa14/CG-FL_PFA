from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone
from django.contrib import messages

from decimal import Decimal
from clientes.models import Cliente, MovimientoCuentaCorriente
from ventas.models import Venta
from contabilidad.models import CierreCaja
from core.models import Sucursal

@login_required
def dashboard_contabilidad(request):
    hoy = timezone.now()
    
    # 1. INGRESOS REALES TOTALES
    ventas_mes = Venta.objects.filter(
        fecha_venta__year=hoy.year, fecha_venta__month=hoy.month, estado='COMPLETADA'
    ).exclude(metodo_pago='CUENTA_CORRIENTE').aggregate(total=Sum('total'))['total'] or Decimal('0.00')

    pagos_cc_mes = MovimientoCuentaCorriente.objects.filter(
        fecha__year=hoy.year, fecha__month=hoy.month, tipo='PAGO'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    ingresos_reales = ventas_mes + pagos_cc_mes

    # 2. DESGLOSE: EFECTIVO VS DIGITAL
    ventas_efectivo = Venta.objects.filter(
        fecha_venta__year=hoy.year, fecha_venta__month=hoy.month, estado='COMPLETADA', metodo_pago='EFECTIVO'
    ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    
    pagos_efectivo = MovimientoCuentaCorriente.objects.filter(
        fecha__year=hoy.year, fecha__month=hoy.month, tipo='PAGO', metodo_pago='EFECTIVO'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    total_efectivo = ventas_efectivo + pagos_efectivo
    total_digital = ingresos_reales - total_efectivo # El resto es banco/MP/Tarjetas

    # 3. PLATA EN LA CALLE
    dinero_en_credito = Cliente.objects.filter(
        saldo_cuenta_corriente__gt=0
    ).aggregate(total=Sum('saldo_cuenta_corriente'))['total'] or Decimal('0.00')

    # 4. GASTOS DE CAJA
    gastos_caja_mes = CierreCaja.objects.filter(
        fecha_cierre__year=hoy.year, fecha_cierre__month=hoy.month
    ).aggregate(total=Sum('efectivo_usado'))['total'] or Decimal('0.00')

    context = {
        'mes_actual': hoy.strftime('%B %Y').capitalize(),
        'ingresos_reales': ingresos_reales,
        'dinero_en_credito': dinero_en_credito,
        'gastos_caja_mes': gastos_caja_mes,
        'total_efectivo': total_efectivo,
        'total_digital': total_digital,
    }
    return render(request, 'contabilidad/dashboard_contabilidad.html', context)


@login_required
def cierre_caja_create(request):
    if request.method == 'POST':
        sucursal_id = request.POST.get('sucursal')
        sucursal = get_object_or_404(Sucursal, id=sucursal_id)
        
        ultimo_cierre = CierreCaja.objects.filter(sucursal=sucursal).order_by('-fecha_cierre').first()
        fecha_inicio = ultimo_cierre.fecha_cierre if ultimo_cierre else timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # 1. SUMAMOS LAS VENTAS NORMALES
        ventas_del_turno = Venta.objects.filter(sucursal=sucursal, fecha_venta__gte=fecha_inicio, estado='COMPLETADA')
        totales_ventas = ventas_del_turno.aggregate(
            efectivo=Sum('total', filter=Q(metodo_pago='EFECTIVO')),
            debito=Sum('total', filter=Q(metodo_pago='DEBITO')),
            credito=Sum('total', filter=Q(metodo_pago='CREDITO')),
            transfer=Sum('total', filter=Q(metodo_pago='TRANSFERENCIA')),
            mpago=Sum('total', filter=Q(metodo_pago='MERCADO_PAGO_QR'))
        )

        # 2. SUMAMOS LOS COBROS DE CUENTA CORRIENTE
        pagos_cc_turno = MovimientoCuentaCorriente.objects.filter(sucursal=sucursal, fecha__gte=fecha_inicio, tipo='PAGO')
        totales_cc = pagos_cc_turno.aggregate(
            efectivo=Sum('monto', filter=Q(metodo_pago='EFECTIVO')),
            debito=Sum('monto', filter=Q(metodo_pago='DEBITO')),
            credito=Sum('monto', filter=Q(metodo_pago='CREDITO')),
            transfer=Sum('monto', filter=Q(metodo_pago='TRANSFERENCIA')),
            mpago=Sum('monto', filter=Q(metodo_pago='MERCADO_PAGO_QR'))
        )

        # 3. UNIMOS AMBOS MUNDOS (Ventas + Cobros CC)
        def sumar_totales(clave):
            v = totales_ventas[clave] or Decimal('0.00')
            c = totales_cc[clave] or Decimal('0.00')
            return v + c

        nuevo_cierre = CierreCaja(
            sucursal=sucursal,
            usuario=request.user,
            fecha_inicio=fecha_inicio,
            
            # Usamos la función auxiliar para sumar las dos fuentes de ingresos
            total_efectivo=sumar_totales('efectivo'),
            total_tarjeta_debito=sumar_totales('debito'),
            total_tarjeta_credito=sumar_totales('credito'),
            total_transferencia=sumar_totales('transfer'),
            total_mercado_pago=sumar_totales('mpago'),
            
            efectivo_declarado=Decimal(request.POST.get('efectivo_declarado', '0.00')),
            efectivo_usado=Decimal(request.POST.get('efectivo_usado', '0.00')),
            observaciones=request.POST.get('observaciones', '')
        )
        nuevo_cierre.save()
        
        messages.success(request, f"¡Caja cerrada en {sucursal.nombre}! Diferencia: ${nuevo_cierre.diferencia_efectivo}")
        return redirect('contabilidad:imprimir_arqueo', cierre_id=nuevo_cierre.id)

    context = {'sucursales': Sucursal.objects.all()}
    return render(request, 'contabilidad/cierre_form.html', context)

@login_required
def historial_cierres(request):
    # Traemos todos los cierres de TODAS las sucursales
    cierres = CierreCaja.objects.all().order_by('-fecha_cierre')
    return render(request, 'contabilidad/historial_cierres.html', {'cierres': cierres})

@login_required
def imprimir_arqueo(request, cierre_id):
    cierre = get_object_or_404(CierreCaja, id=cierre_id)
    ventas_del_turno = Venta.objects.filter(
        sucursal=cierre.sucursal, fecha_venta__gte=cierre.fecha_inicio, 
        fecha_venta__lte=cierre.fecha_cierre, estado='COMPLETADA'
    )
    return render(request, 'contabilidad/ticket_arqueo.html', {'cierre': cierre, 'cantidad_ventas': ventas_del_turno.count()})