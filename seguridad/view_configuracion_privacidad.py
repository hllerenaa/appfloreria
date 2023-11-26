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
from seguridad.forms import ConfiguracionForm, ConfiguracionTerminosForm, ConfiguracionFaqForm, ConfiguracionPrivacidadForm
from seguridad.models import Configuracion


@login_required
@secure_module
def confiPrivacidad(request):
    if Configuracion.objects.count() == 0:
        return redirect('/admin/seguridad/configuracion/add/')
    confi = Configuracion.get_instancia()

    data = {
        'titulo': 'Privacidad {}'.format(confi.nombre_empresa),
        'modulo': 'Configuración',
        'ruta': request.path,
        'fecha': str(date.today())
    }
    addData(request, data)
    model = Configuracion
    Formulario = ConfiguracionPrivacidadForm
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
                            qs_anterior = list(model.objects.filter(pk=confi.pk).values())
                            form = Formulario(request.POST, request.FILES, instance=confi)
                            if form.is_valid():
                                obj = form.save()
                                if request.FILES.get('archivo_manual'):
                                    obj.fecha_reg_manual = datetime.now()
                                    obj.save()
                                salva_auditoria(request, form.instance, 'change',
                                                form.instance.nombre_empresa,
                                                qs_anterior=qs_anterior,
                                                qs_nuevo=list(model.objects.filter(id=form.instance.id).values()))
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
            data["form"] = Formulario(instance=confi)
            data["pk"] = confi.pk
            return render(request, 'seguridad/configuracion/form_privacidad.html', data)
        else:
            return redirect('/')
