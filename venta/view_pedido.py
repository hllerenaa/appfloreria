import json
from datetime import date
from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.utils import timezone

from appfloreria.settings import GMAP_API_KEY
from core.correos_background import enviar_correo_html
from core.custom_models import FormError
from core.decoradores import custom_atomic_request
from core.funciones import addData, paginador, salva_auditoria, redirectAfterPostGet, secure_module, get_decrypt, \
    get_datos_email_html, get_encrypt
from core.funciones_adicionales import customgetattr
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from core.metodos_de_pago import reversar_pago_payphone, reversar_pago_paypal
from mantenimiento.forms import CouriersForm
from .forms import PedidoForm, PedidoEnvioForm
from .models import Pedido, PedidoDetalle, ESTADO_PEDIDO, METODO_PAGOS, HistorialPedido
import os

from django.db.models import Value, Count, Sum, F, FloatField
from django.db.models.functions import Coalesce

@login_required
@secure_module
@custom_atomic_request
def pedidoView(request):
    data = {
        'titulo': 'Pagos Online',
        'modulo': 'Pagos Online',
        'ruta': request.path,
        'fecha': str(date.today()),
    }
    addData(request, data)
    model = Pedido
    nombre_para_audit = '__str__'
    nombre_app, nombre_model = model._meta.app_label, model._meta.model_name
    data["can_add"] = can_add = True
    data["can_change"] = can_change = True
    data["can_delete"] = can_delete = True
    data["can_view"] = can_view = True
    if request.method == 'POST':
        res_json = []
        action = request.POST['action']
        try:
            with transaction.atomic():
                if action == 'pago_pendiente':
                    if can_change:
                        qs_anterior = model.objects.filter(Q(estado="EN_ESPERA"), pk=int(request.POST['pk']))
                        filtro = qs_anterior.first()
                        qs_anterior = list(qs_anterior.values())
                        if filtro:
                            pedido = Pedido.objects.get(id=filtro.id)
                            if not pedido.estado == "EN_ESPERA":
                                raise ValueError("Comprobante ya fue validado, recargue la ventana para confirmar'")
                            ht = HistorialPedido.objects.create(pedido_id=filtro.pk, detalle=request.POST['observacion'], estado=request.POST['estado'], user_id=request.user.pk, archivo=request.FILES.get('archivo'))
                            pedido.estado = ht.estado
                            pedido.save()
                            correos_a_enviar = []
                            subject = 'PAGO #{} {}'.format(pedido.id, pedido.get_estado_display())
                            correos_a_enviar.append(
                                get_datos_email_html({
                                    'titulo': f'Validación de Pago',
                                    'url_compras': "/orders?id={}".format(get_encrypt(pedido.id)[1]), 'pedido': pedido,
                                    "mensaje_correo": 'Tu transacción está con estado "{}".'.format(pedido.get_estado_display()),
                                    "subject": subject,
                                }, pedido.user, subject,
                                    'email/pago_validado.html')
                            )
                            if pedido.estado == "COMPLETADO":
                                pedido.save()
                            salva_auditoria(request, filtro, action,
                                            customgetattr(filtro, nombre_para_audit),
                                            qs_anterior=qs_anterior,
                                            qs_nuevo=list(model.objects.filter(id=filtro.id).values()))
                            for correo in correos_a_enviar:
                                enviar_correo_html(correo)
                            messages.success(request, "Transacción [{}] modificada correctamente.".format(customgetattr(filtro, nombre_para_audit)))
                            res_json.append({'error': False, "to": request.path + "?action=add" if '_add' in request.POST else request.path})
                        else:
                            res_json.append({'error': True,
                                             "message": "Error en el formulario"
                                             })
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'reversar_pago':
                    if can_change:
                        qs_anterior = Pedido.objects.filter(id=int(request.POST['pk']), pago_reversado=False)
                        filtro = qs_anterior.first()
                        qs_anterior = list(qs_anterior.values())
                        if filtro and request.user.is_superuser:
                            if filtro.metodo_pago == "PAYPHONE":
                                response = reversar_pago_payphone(
                                    {
                                        "id": filtro.comprobante
                                    }
                                )
                            elif filtro.metodo_pago == "PAYPAL":
                                comprobante = json.loads(filtro.comprobantejson)
                                response = reversar_pago_paypal(
                                    comprobante["paypalCaptureId"],
                                    comprobante["id"],
                                )
                            if response == True or (isinstance(response, dict) and response.get("status") == "COMPLETED"):
                                filtro.pago_reversado = True
                                filtro.fecha_reversado = timezone.now()
                                filtro.pago_reversado_por_id = request.user.id
                                filtro.razon_reverso = request.POST['razon_reverso']
                                # filtro.estado = "DEVUELTO"
                                filtro.save()
                            else:
                                raise ValueError("Hubo un error al reversar el pago de {} con ID {}".format(filtro.get_metodo_pago_display(), filtro.comprobante))

                            salva_auditoria(request, filtro, action,
                                            customgetattr(filtro, nombre_para_audit),
                                            qs_anterior=qs_anterior,
                                            qs_nuevo=list(Pedido.objects.filter(id=filtro.id).values()))

                            HistorialPedido.objects.create(
                                pedido_id=filtro.id,
                                user_id=request.user.id,
                                estado="DEVUELTO",
                                archivo="",
                                detalle=f"Pago anulado, razón: {request.POST['razon_reverso']}"
                            )

                            messages.success(request, "Transacción [{}] reversado correctamente.".format(customgetattr(filtro, "__str__")))
                            res_json.append({'error': False, "to": request.path + "?action=add" if '_add' in request.POST else request.path})

                        else:
                            res_json.append({'error': True,
                                             "message": "Error en el formulario"
                                             })
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'anular_pedido':
                    if can_change:
                        qs_anterior = Pedido.objects.filter(id=int(request.POST['pk']))
                        filtro = qs_anterior.first()
                        qs_anterior = list(qs_anterior.values())
                        if filtro and request.user.is_superuser:
                            filtro.estado = "ANULADO"
                            filtro.save()
                            # for l in filtro.get_detalle():
                            #     l.retirar(request)
                            ht = HistorialPedido.objects.create(pedido_id=filtro.pk,
                                                                detalle=request.POST['detalle'],
                                                                estado="ANULADO", user_id=request.user.pk,
                                                                archivo=request.FILES.get('archivo'))
                            salva_auditoria(request, filtro, action,
                                            customgetattr(filtro, nombre_para_audit),
                                            qs_anterior=qs_anterior,
                                            qs_nuevo=list(Pedido.objects.filter(id=filtro.id).values()))
                            messages.success(request, "Transacción [{}] anulada correctamente.".format(customgetattr(filtro, "__str__")))
                            res_json.append({'error': False, "to": request.path + "?action=add" if '_add' in request.POST else request.path})

                        else:
                            res_json.append({'error': True,
                                             "message": "Error en el formulario"
                                             })
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'addcouriers':
                    filtro = Pedido.objects.get(pk=int(request.POST['pk']))
                    form = PedidoForm(request.POST, request.FILES, instance=filtro)
                    if form.is_valid():
                        form.instance.estado_entrega = 'ENVIADO'
                        form.save()
                        ht = HistorialPedido.objects.create(pedido_id=filtro.pk,
                                                            detalle=f"Enviado al cliente con {form.cleaned_data['couriers']}",
                                                            estado="ENVIADO", user_id=request.user.pk,
                                                            archivo=request.FILES.get('archivo_entrega'))
                        res_json.append({'error': False, "reload": True})
                    else:
                        raise FormError(form)
                elif action == 'changeestadoenvio':
                    filtro = Pedido.objects.get(pk=int(request.POST['pk']))
                    form = PedidoEnvioForm(request.POST, request.FILES, instance=filtro)
                    if form.is_valid():
                        form.save()
                        ht = HistorialPedido.objects.create(pedido_id=filtro.pk,
                                                            detalle=f"Pedido fue {form.cleaned_data['estado_entrega']}",
                                                            estado=form.cleaned_data['estado_entrega'], user_id=request.user.pk,
                                                            archivo=request.FILES.get('archivo_entrega'))
                        res_json.append({'error': False, "reload": True})
                    else:
                        raise FormError(form)
        except Exception as ex:
            res_json.append({'error': True,
                             "message": f"Intente Nuevamente, {ex}"
                             })
        return JsonResponse(res_json, safe=False)
    elif request.method == 'GET':
        if 'action' in request.GET:
            data["action"] = action = request.GET['action']
            if action == 'pago_pendiente':
                pk = int(request.GET['pk'])
                instancia = model.objects.get(pk=pk)
                data["pk"] = pk
                data["obj"] = instancia
                data["compra"] = instancia
                data["detallepedido"] = instancia.get_detalle()
                return render(request, 'venta/pedido/pago_pendiente.html', data)
            elif action == "historial_pedido":
                pk = int(get_decrypt(request.GET['pk'])[1])
                data['pedido'] = pedido = Pedido.objects.get(id=pk)
                data["historial"] = historial = HistorialPedido.objects.filter(status=True, pedido_id=pk).order_by('pk')
                template = get_template('venta/pedido/historial_pedido.html')
                return JsonResponse({"result": True, 'data': template.render(data), 'titulo': 'PAGO #{} - {}'.format(pk, pedido.user.get_full_name())})
            elif action == "historial_orden":
                pk = int(get_decrypt(request.GET['pk'])[1])
                data['pedido'] = pedido = Pedido.objects.get(id=pk)
                data["historial"] = historial = HistorialPedido.objects.filter(status=True, pedido_id=pk).order_by('pk')
                data['start_lat'] = start_lat = str(data['confi'].latitud)
                data['start_lon'] = start_lon = str(data['confi'].longitud)
                data['dest_lat'] = dest_lat = str(pedido.latitud)
                data['dest_lon'] = dest_lon = str(pedido.longitud)
                limite_envio = data['confi'].limite_km_envio
                data['limite_envio'] = str(limite_envio)
                template = get_template('venta/pedido/historial_orden.html')
                return JsonResponse({"result": True, 'data': template.render(data), 'titulo': 'PAGO #{} - {}'.format(pk, pedido.user.get_full_name())})
            elif action == 'detalle':
                if can_add:
                    data["compra"] = Pedido.objects.get(id=request.GET['pk'], status=True)
                    data["detallepedido"] = PedidoDetalle.objects.filter(pedido_id=request.GET['pk'], status=True)
                    return render(request, 'venta/pedido/detalle.html', data)
                else:
                    messages.error(request, "No tienes permisos para agregar registros")
                    return redirect(redirectAfterPostGet(request))
            elif action == "anular_pedido":
                pk = int(get_decrypt(request.GET['pk'])[1])
                instancia = Pedido.objects.get(pk=pk)
                data["pk"] = pk
                data["compra"] = instancia
                return render(request, 'venta/pedido/anular_pedido.html', data)
            elif action == "reversar_pago":
                pk = int(get_decrypt(request.GET['pk'])[1])
                instancia = Pedido.objects.get(pk=pk)
                if request.user.is_superuser and instancia.es_pago_electronico and not instancia.pago_reversado:
                    data["pk"] = pk
                    data["compra"] = instancia
                    return render(request, 'venta/pedido/reversar_pago.html', data)
                else:
                    messages.success(request, f"Acción no permitida")
                    return redirect('/')
            elif action == 'addcouriers':
                try:
                    data['id'] = id = int(request.GET['pk'])
                    data['filtro'] = filtro = Pedido.objects.get(pk=id)
                    form = PedidoForm()
                    data['form'] = form
                    template = get_template("venta/pedido/formmodal.html")
                    return JsonResponse({"result": True, 'data': template.render(data), 'titulo': 'Asignar Courier #{} - {}'.format(id, filtro.user.get_full_name())})
                except Exception as ex:
                    pass
            elif action == 'changeestadoenvio':
                try:
                    data['id'] = id = int(request.GET['pk'])
                    data['filtro'] = filtro = Pedido.objects.get(pk=id)
                    form = PedidoEnvioForm()
                    data['form'] = form
                    template = get_template("venta/pedido/formmodal.html")
                    return JsonResponse({"result": True, 'data': template.render(data), 'titulo': 'Cambiar Estado de Entrega #{} - {}'.format(id, filtro.user.get_full_name())})
                except Exception as ex:
                    pass
        if can_view:
            id, criterio, fecha_desde, fecha_hasta, filtros, url_vars = request.GET.get('id', ''),  request.GET.get('criterio', '').strip(), request.GET.get('fecha_desde', ''),request.GET.get('fecha_hasta', ''), (Q(status=True) ), ''
            metodopago, estado = request.GET.get('metodopago', '').strip(), request.GET.get('estado', '').strip()
            if criterio:
                filtros = filtros & (Q(user__first_name__icontains=criterio) | Q(user__last_name__icontains=criterio))
                data["criterio"] = criterio
                url_vars += '&criterio=' + criterio
            if metodopago:
                filtros = filtros & (Q(metodopago=metodopago))
                data["metodopago"] = metodopago
                url_vars += '&metodopago=' + metodopago
            if estado:
                filtros = filtros & (Q(estado=estado))
                data["estado"] = estado
                url_vars += '&estado=' + estado
            if fecha_desde:
                filtros = filtros & Q(fecha_registro__gte=fecha_desde)
                data["fecha_desde"] = fecha_desde
                url_vars += '&fecha_desde=' + fecha_desde
            if fecha_hasta:
                filtros = filtros & Q(fecha_registro__lte=fecha_hasta)
                data["fecha_hasta"] = fecha_hasta
                url_vars += '&fecha_hasta=' + fecha_hasta
            if id:
                filtros = filtros & Q(id=id)
                data["id"] = id
                url_vars += f'&id={id}'
            listado = Pedido.objects.filter(filtros).exclude(estado='GUARDADO').order_by('-pk')
            data["url_vars"] = url_vars
            data["pag"] = pag = 10
            paginador(request, listado, pag, data, url_vars)
            data['METODO_PAGOS'] = METODO_PAGOS
            data['ESTADO_PEDIDO'] = ESTADO_PEDIDO[1:]
            data["list_count"] = len(listado)
            data["GMAP_API_KEY"] = GMAP_API_KEY
            data['totalreversado'] = totalreversado = listado.filter(pago_reversado=True).aggregate(total=Coalesce(Sum(F('total'), output_field=FloatField()), 0)).get('total')
            data['totalvalido'] = totalvalido = listado.filter(pago_reversado=False).aggregate(total=Coalesce(Sum(F('total'), output_field=FloatField()), 0)).get('total')
            data['totalrecaudado'] = totalrecaudado = listado.aggregate(total=Coalesce(Sum(F('total'), output_field=FloatField()), 0)).get('total')
            return render(request, 'venta/pedido/listado.html', data)
        else:
            messages.error(request, "No tienes permisos para ver registros")
            return redirect('/')