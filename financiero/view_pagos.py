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
# from emarket.settings import EMAIL_HOST_USER
# from mantenimiento.models import FichaTecnica
# from .forms import HistorialTransaccionForm
# from .models import Transaccion, HistorialTransaccion, Billetera
# from django.contrib import messages
#
# @login_required
# @secure_module
# def pagosAprobadosView(request):
#     data = {'titulo': 'Pagos Aprobados',
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
#                 pass
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
#             criterio, filtros, url_vars = request.GET.get('criterio', ''), (Q(status=True) & Q(estado="APROBADO") & Q(razon_tr__in=("COMPRA", "PAGO_A_EMPRESA", "PAGO_MEMBRESIA"))), ''
#             if criterio:
#                 filtros = filtros & Q(nombre__icontains=criterio)
#                 data["criterio"] = criterio
#                 url_vars += '&criterio=' + criterio
#             listado = model.objects.filter(filtros)
#             data['total_pagos'] = listado.aggregate(total_pagos=Sum('valor')).get('total_pagos') or 0
#             data["url_vars"] = url_vars
#             mi_paginador(request, listado, 40, data)
#             return render(request, 'financiero/pagos/listado.html', data)
#         else:
#             messages.error(request, "No tienes permisos para ver {}".format(data["titulo"]))
#             return redirect('/')