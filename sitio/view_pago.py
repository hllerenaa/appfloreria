import uuid

import requests
from _decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.constantes import CONFIRM_PAYPHONE_URL
from core.custom_models import ExecFunctionError, FormError
from core.decoradores import custom_atomic_request
from core.email_config import send_html_mail
from core.funciones import addData, get_decrypt, get_encrypt, get_client_ip
from core.funciones_adicionales import round_num_dec
from core.metodos_de_pago import request_completar_pago_paypal
from financiero.models import CuentaFinancieraEmpresa
from appfloreria import settings
from appfloreria.settings import URL_GENERAL, JS_PAYPAL_URL, JS_PAYPAL_URL_TEST, PAYPAL_ST
from seguridad.models import SessionUser
from sitio.forms import PedidoArchivoPagoForm
from venta.models import Pedido, PedidoDetalle, PagoTransferencia, HistorialPedido


@login_required(login_url='/login/')
@custom_atomic_request
def pagoView(request, pedido_id):
    data = {
        'titulo': 'Pagar Orden',
        'modulo': 'Pedido',
        'ruta': request.path,
    }
    if not get_decrypt(pedido_id)[0]:
        return redirect('/shop/')
    pedido_id = get_decrypt(pedido_id)[1]
    addData(request, data)
    if not Pedido.objects.values('id').filter(id=pedido_id, user_id=request.user.id, estado="GUARDADO"):
        messages.warning(request, f'Transacción ya completada')
        return redirect('/catalogo/')
    data['pedido'] = pedido = Pedido.objects.get(id=pedido_id, user_id=request.user.id, estado="GUARDADO")
    data['detallePedido'] = detallePedido = PedidoDetalle.objects.filter(pedido_id=pedido_id)
    data['producto'] = producto = detallePedido.first().item

    if request.method == 'POST':
        res_json = []
        action = request.POST.get('action')
        if action == 'pagar':
            if pedido.metodo_pago == "TRANSFERENCIA_BANCARIA":
                f = PedidoArchivoPagoForm(request.POST, request.FILES, instance=pedido)
                # pedido.session_user_id = SessionUser.nuevo(request)
                if f.is_valid():
                    pedido.ip = get_client_ip(request)
                    pedido.modo_pago = True
                    pedido.entidad_fin_id = request.POST['entidad_fin']
                    pedido.archivo_pago = request.FILES['archivo_pago']
                    pedido.estado = "EN_ESPERA"
                    pedido.save()
                    PagoTransferencia.objects.create(
                        modelo=pedido,
                        infobanco="Banco {}, con número de tipo de cuenta {} {}".format(
                            pedido.entidad_fin.ent_fin.nombre, pedido.entidad_fin.get_tipo_display(),
                            pedido.entidad_fin.num_cuenta),
                        infopersona=pedido.entidad_fin.nombres
                    )
                    messages.success(request, f"Nos complace informarle que su compra está siendo procesada, en unos momentos tendremos respuesta.")
                else:
                    raise FormError(f)
            elif pedido.metodo_pago == "PAYPAL":
                pedido.modo_pago = request.config.paypal_modo
                pedido.estado = "EN_ESPERA"
                pedido.save()
                request_completar_pago_paypal(data, request, pedido)
                messages.success(request, "Estamos procesando tu pedido, te avisaremos en unos instantes")
            pedido.save()

            if pedido.metodo_pago != "PAYPAL":
                HistorialPedido.objects.create(
                    pedido_id=pedido.id,
                    user_id=request.user.id,
                    estado=pedido.estado,
                    archivo=pedido.archivo_pago,
                    detalle="PAGO #{} {}{} PAGADO CON {}, ESTADO: {}".format(pedido.id, data["SIMBOLO_MONEDA"],
                                                                               pedido.total,
                                                                               pedido.get_metodo_pago_display(),
                                                                               pedido.get_estado_display())
                )


            datos = {
                'sucursal': data['confi'].nombre_empresa,
                'correo': str(settings.EMAIL_HOST_USER),
                'pedido': pedido,
                'producto': producto,
                'url': f'{data["DOMINIO_DEL_SISTEMA"]}/ventas/pedidos/',
            }
            subject = f'¡Acabas de recibir un nuevo pago por el producto. {producto}!'
            to = data['confi'].email
            send_html_mail(subject, "email/interesado_curso.html", datos, [to], [], [])
            if 'carrito' in request.session:
                del request.session['carrito']
            if 'dict_orden' in request.session:
                del request.session['dict_orden']
            if 'total' in request.session:
                del request.session['total']
            res_json.append(
                {
                    "to": "/orders/",
                }
            )
        return JsonResponse(res_json, safe=False)
    if request.method == 'GET':
        if 'action' in request.GET:
            data["action"] = action = request.GET["action"]
        data['amount'] = round_num_dec(pedido.total * Decimal('100'), 0)
        data['randomid'] = str(uuid.uuid1())
        if pedido.metodo_pago == 'TRANSFERENCIA_BANCARIA':
            data['cuentas'] = CuentaFinancieraEmpresa.objects.filter(status=True)
            return render(request, 'sitio/carrito/pago_transferencia.html', data)
        elif pedido.metodo_pago == 'PAYPAL':
            if not PAYPAL_ST:
                messages.warning(request, f'Payment method not available at the moment')
                return redirect('/shop/')
            if data['confi'].paypal_modo:
                data['JS_PAYPAL_URL'] = JS_PAYPAL_URL
            else:
                data['JS_PAYPAL_URL'] = JS_PAYPAL_URL_TEST
            data['clientTransactionId'] = str(pedido.pk)
            data['documentId'] = pedido.user.id
            data['email'] = pedido.user.email
            return render(request, 'sitio/carrito/pago_paypal.html', data)
        else:
            messages.warning(request, f'Método de pago no disponible por el momento')
            return redirect('/shop/')