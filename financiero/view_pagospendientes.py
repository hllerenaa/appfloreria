# from datetime import date
# from decimal import Decimal
#
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
# from django.db import transaction
# from django.db.models import Q, Sum
# from django.db.models.functions import Coalesce
# from django.http import JsonResponse
# from django.shortcuts import render, redirect
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
#
# from core.correos_background import enviar_correo_html
# from core.funciones import addData, mi_paginador, salva_auditoria, secure_module, get_encrypt, salva_auditoriacliente, \
#     get_decrypt
# from core.funciones_adicionales import customgetattr
# from prytalis.settings import EMAIL_HOST_USER
# from mantenimiento.models import ProductoStock
# from venta.models import HistorialPedido
# from .forms import HistorialTransaccionForm
# from .models import Transaccion, HistorialTransaccion, Billetera
# from django.contrib import messages
#
# @login_required
# @secure_module
# def pedidosPendientesView(request):
#     data = {'titulo': 'Pagos Pendientes',
#             'modulo': 'Recaudación',
#             'ruta': request.path,
#
#             }
#     addData(request, data)
#     model = Transaccion
#     Formulario = HistorialTransaccionForm
#     nombre_para_audit = '__str__'
#     nombre_app, nombre_model = model._meta.app_label, model._meta.model_name
#     data["can_add"] = can_add = True
#     data["can_change"] = can_change = True
#     data["can_delete"] = can_delete = True
#     data["can_view"] = can_view = True
#     if request.method == 'POST':
#         res_json = []
#         action = request.POST['action']
#         try:
#             with transaction.atomic():
#                 if action == 'pago_pendiente':
#                     if can_change:
#                         qs_anterior = model.objects.filter(Q(estado="PENDIENTE") & Q(razon_tr__in=("COMPRA", "PAGO_A_EMPRESA", "RETIRO_BANCO")), pk=int(request.POST['pk']))
#                         filtro = qs_anterior.first()
#                         qs_anterior = list(qs_anterior.values())
#                         form = Formulario(request.POST)
#                         if form.is_valid() and filtro:
#                             if request.POST['estado'] == "PENDIENTE":
#                                 raise ValueError("El estado no debe ser 'Pendiente'")
#                             ht = HistorialTransaccion.objects.create(transaccion_id=filtro.pk, observacion=request.POST['observacion'], estado=request.POST['estado'], user_id=request.user.pk)
#                             filtro.estado = ht.estado
#                             filtro.observacion = ht.observacion
#                             filtro.save()
#
#                             correos_a_enviar = []
#                             correo_usuario = EMAIL_HOST_USER
#                             empresa = data['nombreempresa']
#                             datos = {
#                                 'empleado': filtro.user.usuarios.datos(),
#                                 'correo': str(correo_usuario),
#                                 'nombreempresa': empresa,
#                                 'url_compras': filtro.get_url_transaccion() if filtro.estado == "APROBADO" else "/transaccion/?action=corregir_transaccion&pk={}".format(get_encrypt(filtro.pk)[1]) if filtro.estado == "EN_CORRECCION" else "/transaccion/",
#                                 "msg_pedido": "transacción",
#                                 'mensaje_correo': 'Tu transacción está con estado "{}".'.format(filtro.get_estado_display())
#                             }
#                             subject = 'TRANSACCION {}'.format(filtro.get_estado_display())
#                             html_message = render_to_string('email/compra_usuario.html', datos)
#                             plain_message = strip_tags(html_message)
#                             from_email = empresa
#                             to = filtro.user.email
#                             correos_a_enviar.append(
#                                 {"subject": subject, "plain_message": plain_message, "from_email": from_email,
#                                  "to": [to],
#                                  "html_message": html_message})
#
#                             if filtro.estado == "APROBADO" and filtro.razon_tr == "COMPRA":
#                                 pedido = filtro.get_instancia_transaccion()
#                                 pedido.pagado = True
#                                 pedido.estado = "PROCESADO"
#                                 pedido.save()
#                                 det_ped = pedido.detallepedido_set.all()
#                                 #se actualiza el estado en el detalle del pedido
#                                 det_ped.update(estado=pedido.estado)
#                                 users = list(det_ped.values_list('ficha__usuario_id',flat=True).order_by('ficha__usuario_id').distinct())
#
#                                 for vp in users:
#                                     histPed = HistorialPedido.objects.create(
#                                         user_id=request.user.pk,
#                                         detalle=ht.observacion.upper(),
#                                         archivo=pedido.archivo_pago,
#                                         estado=pedido.estado
#                                     )
#
#                                     for dp in det_ped.filter(ficha__usuario_id=vp):
#                                         histPed.detallepedido.add(dp)
#
#                                 prod_sin_stock = []
#
#                                 for dp in det_ped:
#                                     ficha = FichaTecnica.objects.get(pk=dp.ficha.pk)
#                                     cat = ficha.subcategoria.categoria
#                                     if ficha.activo:
#                                         if cat.tipo == cat.PRODUCTOS_Y_OTROS or cat.tipo == cat.SERVICIOS:
#                                             if cat.tipo == cat.PRODUCTOS_Y_OTROS:
#                                                 if (ficha.cantidad - dp.cantidad) < 0:
#                                                     prod_sin_stock.append(ficha.titulo)
#                                                 else:
#                                                     ficha.cantidad = ficha.cantidad - dp.cantidad
#                                                     ficha.save()
#                                     else:
#                                         prod_sin_stock.append(ficha.titulo)
#
#                                 if len(prod_sin_stock) > 0:
#                                     raise ValueError("Los items [{}], no están disponibles.".format(", ".join(prod_sin_stock)))
#
#                                 for id in users:  # Los users son del detalle del pedido, porq cada producto puede ser de diferentes vendedores
#                                     valores = det_ped.filter(ficha__usuario_id=id).aggregate(
#                                         totales=Coalesce(Sum('total'), Decimal('0')), tarifas=Coalesce(Sum('totalimpuestos'), Decimal('0')))
#
#                                     totalPagado = valores['totales']+valores['tarifas']
#
#                                     objUser = User.objects.get(pk=int(id))
#
#                                     tr = Transaccion.objects.create(user_id=id, comprobante_tr=str(pedido.id),
#                                                                tipo_tr="INGRESO", razon_tr="VENTA",
#                                                                valor=totalPagado,
#                                                                metodo_pago=pedido.metodo_pago,
#                                                                archivo=pedido.archivo_pago,
#                                                                estado="APROBADO",
#                                                                observacion=pedido.especificaciones_pedido)
#
#                                     wall = Billetera.objects.create(user_id=id, user_transaccion_id=pedido.user.pk,
#                                              comprobante_tr=str(pedido.id), tipo_tr="INGRESO",
#                                              razon_tr="VENTA", valor=totalPagado,
#                                              saldo_anterior=Billetera.objects.filter(user_id=id,
#                                                                                      estado="APROBADO").aggregate(
#                                                  totales=Coalesce(Sum('valor'), Decimal('0'))).get(
#                                                  'totales') or Decimal('0'),
#                                              estado="APROBADO")
#
#                                     salva_auditoriacliente(request, tr, request.acciones_estudiante.VENTA, tr.__str__(), theuser=objUser)
#
#                                     salva_auditoriacliente(request, wall, request.acciones_estudiante.INGRESO_DINERO_WALLET, wall.__str__(),
#                                                            theuser=objUser)
#
#                                     correo_usuario = EMAIL_HOST_USER
#                                     empresa = data['nombreempresa']
#                                     datos = {
#                                         'empleado': objUser.usuarios.datos(),
#                                         'correo': str(correo_usuario),
#                                         'nombreempresa': empresa,
#                                         'url_compras': "/ventas/detalle/{}/".format(get_encrypt(pedido.pk)[1]),
#                                         "msg_pedido": "venta"
#                                     }
#                                     subject = ""
#                                     datos['mensaje_correo'] = "Nos complace decirte que tienes una nueva venta."
#                                     subject = 'VENTA REALIZADA'
#                                     html_message = render_to_string('email/compra_usuario.html', datos)
#                                     plain_message = strip_tags(html_message)
#                                     from_email = empresa
#                                     to = objUser.email
#                                     correos_a_enviar.append(
#                                         {"subject": subject, "plain_message": plain_message, "from_email": from_email,
#                                          "to": [to],
#                                          "html_message": html_message})
#                             elif filtro.estado == "RECHAZADO" and filtro.razon_tr == "COMPRA":
#                                 pedido = filtro.get_instancia_transaccion()
#                                 pedido.pagado = False
#                                 pedido.estado = "ANULADO"
#                                 pedido.save()
#                                 # se actualiza el estado en el detalle del pedido
#                                 pedido.detallepedido_set.all().update(estado=pedido.estado)
#                             salva_auditoria(request, filtro, action,
#                                             customgetattr(filtro, nombre_para_audit),
#                                             qs_anterior=qs_anterior,
#                                             qs_nuevo=list(model.objects.filter(id=filtro.id).values()))
#                             for correo in correos_a_enviar:
#                                 enviar_correo_html(correo)
#
#                             messages.success(request, "Transacción [{}] modificada correctamente.".format(
#                                 customgetattr(filtro, nombre_para_audit)))
#                             res_json.append({'error': False,
#                                              "to": request.path + "?action=add" if '_add' in request.POST else request.path
#                                              })
#
#                         else:
#                             res_json.append({'error': True,
#                                              "form": [{k: v[0]} for k, v in form.errors.items()],
#                                              "message": "Error en el formulario"
#                                              })
#                     else:
#                         res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
#         except ValueError as ex:
#             res_json.append({'error': True,
#                              "message": str(ex)
#                              })
#         except Exception as ex:
#             res_json.append({'error': True,
#                              "message": "Intente Nuevamente"
#                              })
#         return JsonResponse(res_json, safe=False)
#     elif request.method == 'GET':
#         if 'action' in request.GET:
#             data["action"] = action = request.GET['action']
#             if action == 'pago_pendiente':
#                 if can_change:
#                     pk = int(request.GET['pk'])
#                     instancia = model.objects.get(pk=pk)
#                     data["pk"] = pk
#                     data["obj"] = instancia
#                     return render(request, 'financiero/transaccion/pago_pendiente.html', data)
#                 else:
#                     messages.error(request, "No tienes permisos para modificar {}".format(data["titulo"]))
#                     return redirect(request.path)
#             elif action == 'historial_transaccion':
#                 pk = int(get_decrypt(request.GET['pk'])[1])
#                 data['obj'] = instancia = model.objects.get(pk=pk)
#                 data['historial'] = instancia.historialtransaccion_set.filter(status=True).order_by('pk')
#                 data["pk"] = request.GET['pk']
#                 return JsonResponse({"status": True,
#                                      "content_historial": render_to_string('tienda/transacciones/historial_transaccion.html', data)})
#         if can_view:
#             criterio, filtros, url_vars = request.GET.get('criterio', ''), (Q(status=True) & Q(estado="PENDIENTE") & Q(razon_tr__in=("COMPRA", "PAGO_A_EMPRESA", "RETIRO_BANCO"))), ''
#             if criterio:
#                 filtros = filtros & Q(nombre__icontains=criterio)
#                 data["criterio"] = criterio
#                 url_vars += '&criterio=' + criterio
#             listado = model.objects.filter(filtros)
#             data["url_vars"] = url_vars
#             mi_paginador(request, listado, 40, data)
#             return render(request, 'financiero/transaccion/listado.html', data)
#         else:
#             messages.error(request, "No tienes permisos para ver {}".format(data["titulo"]))
#             return redirect('/')