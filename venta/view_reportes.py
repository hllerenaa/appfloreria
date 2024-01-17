import json
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect
from core.funciones import addData, salva_auditoria, secure_module
from seguridad.models import ModuloGrupo, Modulo
from django.contrib import messages

from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from venta.models import Pedido, PedidoDetalle


@login_required
@secure_module
def reportesView(request):
    data = {'titulo': 'Reportes',
            'modulo': 'Reportes',
            'ruta': request.path,
            'ruta_val': request.path,
            'group': 'Seguridad',
            'fecha': str(date.today())
            }
    addData(request, data)
    if request.method == 'POST':
        res_json = []
        action = request.POST['action']

    elif request.method == 'GET':
        fecha_desde, fecha_hasta, filtros, url_vars = request.GET.get('fecha_desde', ''), request.GET.get('fecha_hasta', ''), (Q(status=True)), ''
        if fecha_desde:
            filtros = filtros & Q(fecha_registro__gte=fecha_desde)
            data["fecha_desde"] = fecha_desde
            url_vars += '&fecha_desde=' + fecha_desde
        if fecha_hasta:
            filtros = filtros & Q(fecha_registro__lte=fecha_hasta)
            data["fecha_hasta"] = fecha_hasta
            url_vars += '&fecha_hasta=' + fecha_hasta

        listado = Pedido.objects.filter(filtros).exclude(estado='GUARDADO').order_by('-pk')

        clientes_con_pedidos = listado.values('user').annotate(numero_pedidos=Count('id', distinct=True),
                                                               total_monetario=Sum('total')).filter(numero_pedidos__gt=0).order_by('user')

        totales_por_metodo = listado.values('metodo_pago').annotate(
            total_recaudado=Sum('total'),
            cantidad=Count('id')
        ).order_by('-total_recaudado')

        ciudades = listado.values('city').annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')

        seis_meses_atras = timezone.now() - timedelta(days=6 * 30)

        totales_por_mes = Pedido.objects.filter(
            fecha_registro__gte=seis_meses_atras
        ).annotate(
            mes=TruncMonth('fecha_registro')
        ).values('mes').annotate(
            total_recaudado=Sum('total')
        ).order_by('mes')

        productos_mas_solicitados = PedidoDetalle.objects.filter(pedido__in=listado.values_list('id',flat=True)).values('item__nombre', 'item__foto1').annotate(cantidad_total=Sum('cantidad')).order_by('-cantidad_total')

        data['ciudades'] = ciudades
        data['totales_por_metodo'] = totales_por_metodo
        data['clientes_con_pedidos'] = clientes_con_pedidos
        data['totales_por_mes'] = totales_por_mes
        data['productos_mas_solicitados'] = productos_mas_solicitados[:10]
        return render(request, 'seguridad/reportes/listado.html', data)
