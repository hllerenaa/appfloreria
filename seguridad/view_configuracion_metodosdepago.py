import sys
from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.custom_models import FormError
from core.funciones import addData, salva_auditoria, secure_module
from core.funciones_adicionales import salva_logs
from seguridad.forms import ConfiguracionForm, ConfiguracionTerminosForm, ConfiguracionMetodosDePagoForm, ConfiguracionPrivacidadForm
from seguridad.models import Configuracion


@login_required
@secure_module
def confiMetodosDePago(request):
    if Configuracion.objects.count() == 0:
        return redirect('/admin/seguridad/configuracion/add/')
    confi = Configuracion.get_instancia()

    data = {
        'titulo': 'Métodos de pago {}'.format(confi.nombre_empresa),
        'modulo': 'Configuración',
        'ruta': request.path,
        'fecha': str(date.today())
    }
    addData(request, data)
    model = Configuracion
    nombre_app, nombre_model = model._meta.app_label, model._meta.model_name
    data["can_add"] = can_add = True
    data["can_change"] = can_change = True
    data["can_delete"] = can_delete = True
    data["can_view"] = can_view = True
    if request.method == 'POST':
        res_json = []
        if 'action' in request.POST:
            action = request.POST["action"]
            try:
                with transaction.atomic():
                    if action == 'change':
                        if can_change:
                            qs_anterior = list(Configuracion.objects.filter(pk=confi.pk).values())
                            form = ConfiguracionMetodosDePagoForm(request.POST, request.FILES, instance=confi)
                            if not data['PAYPHONE_ST']:
                                del form.fields['payphone_modo']
                            if not data['PAYPAL_ST']:
                                del form.fields['paypal_modo']
                            if form.is_valid():
                                obj = form.save()
                                salva_auditoria(request, form.instance, 'change',
                                                form.instance.nombre_empresa,
                                                qs_anterior=qs_anterior,
                                                qs_nuevo=list(Configuracion.objects.filter(id=form.instance.id).values()))
                                res_json.append({'error': False,
                                                 "to": request.path
                                                 })
                                messages.success(request, "Modificado correctamente.")
                            else:
                                raise FormError(form)
                        else:
                            res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
            except ValueError as ex:
                res_json.append({'error': True,
                                 "message": str(ex)
                                 })
            except FormError as ex:
                res_json.append(ex.dict_error)
            except Exception as ex:
                salva_logs(request, __file__, request.method,
                           action, type(ex).__name__,
                           'Error on line {}'.format(sys.exc_info()[-1].tb_lineno), ex)
                res_json.append({'error': True,
                                 "message": "Intente Nuevamente"
                                 })
        return JsonResponse(res_json, safe=False)
    elif request.method == 'GET':
        if can_view:
            form = ConfiguracionMetodosDePagoForm(instance=confi)
            if not data['PAYPHONE_ST']:
                del form.fields['payphone_modo']
            if not data['PAYPAL_ST']:
                del form.fields['paypal_modo']
            data["form"] = form
            data["pk"] = confi.pk
            return render(request, 'seguridad/configuracion/form_metodopago.html', data)
        else:
            return redirect('/')
