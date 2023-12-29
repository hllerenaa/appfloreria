from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import get_template

from core.funciones import addData, paginador, get_decrypt
from venta.models import Pedido, HistorialPedido


@login_required
def orderView(request):
    data = {
        'titulo': "Mis Pagos",
        'modulo': 'Perfil',
        'ruta': request.path,
    }
    addData(request, data)

    if request.method == 'POST':
        res_json = []
    else:
        if 'action' in request.GET:
            data['action'] = action = request.GET['action']
            if action == "historial_pedido":
                pk = int(get_decrypt(request.GET['pk'])[1])
                data['pedido'] = pedido = Pedido.objects.get(id=pk)
                data["historial"] = historial = HistorialPedido.objects.filter(status=True, pedido_id=pk).order_by('pk')
                template = get_template('sitio/perfil/historial_pedido.html')
                return JsonResponse({"result": True, 'data': template.render(data),
                                     'titulo': 'Orden #{} - {}'.format(pk, pedido.user.get_full_name())})
            elif action == "detalle_pedido":
                pk = int(get_decrypt(request.GET['pk'])[1])
                data['pedido'] = pedido = Pedido.objects.get(id=pk)
                template = get_template('venta/pedido/detalle_pedido.html')
                return JsonResponse({"result": True, 'data': template.render(data), 'titulo': 'PAGO #{} - {}'.format(pk, pedido.user.get_full_name())})

    estado, filtros = request.GET.get('est', '') , Q(status=True)

    if estado:
        filtros = filtros & Q(estado=estado)

    pedidos = Pedido.objects.filter(user=request.user).filter(filtros).exclude(estado='GUARDADO').order_by('-pk')
    paginador(request, pedidos, 10, data, url_vars='')
    data['existe_en_espera'] = existe_en_espera = Pedido.objects.values('id').filter(user=request.user, estado='EN_ESPERA', metodo_pago='PAYPAL').order_by('-pk')
    return render(request, 'sitio/perfil/orders.html', data)
