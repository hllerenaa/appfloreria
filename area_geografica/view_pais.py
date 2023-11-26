from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.custom_models import FormError
from core.funciones import addData, paginador, salva_auditoria, secure_module, redirectAfterPostGet
from .forms import PaisForm
from .models import Pais
from django.contrib import messages
from core.funciones_adicionales import salva_logs, customgetattr
import sys


@login_required
@secure_module
def paisView(request):
    data = {'titulo': 'Países',
            'modulo': 'Área Geográfica',
            'ruta': request.path,
            'fecha': str(date.today())
            }
    model = Pais
    Formulario = PaisForm
    nombre_para_audit = 'nombre'
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
                if action == 'add':
                    if can_add:
                        form = Formulario(request.POST)
                        if form.is_valid():
                            form.save()
                            salva_auditoria(request, form.instance, action,
                                            customgetattr(form.instance, nombre_para_audit),
                                            qs_nuevo=list(model.objects.filter(id=form.instance.id).values()))
                            messages.success(request,
                                             "{} agregado".format(customgetattr(form.instance, nombre_para_audit)))
                            res_json.append({'error': False,
                                             "to": redirectAfterPostGet(request)
                                             })
                        else:
                            raise FormError(form)
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'change':
                    if can_change:
                        qs_anterior = model.objects.filter(pk=int(request.POST['pk']))
                        filtro = qs_anterior.first()
                        qs_anterior = list(qs_anterior.values())
                        form = Formulario(request.POST, instance=filtro)
                        if form.is_valid() and filtro:
                            form.save()
                            salva_auditoria(request, form.instance, action,
                                            customgetattr(form.instance, nombre_para_audit),
                                            qs_anterior=qs_anterior,
                                            qs_nuevo=list(model.objects.filter(id=form.instance.id).values()))
                            messages.success(request,
                                             "{} agregado".format(customgetattr(form.instance, nombre_para_audit)))
                            res_json.append({'error': False,
                                             "to": redirectAfterPostGet(request)
                                             })
                        else:
                            raise FormError(form)
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'delete':
                    if can_delete:
                        qs_anterior = model.objects.filter(pk=int(request.POST['id']))
                        filtro = qs_anterior.first()
                        qs_anterior = list(qs_anterior.values())
                        filtro.status = False
                        filtro.save()
                        salva_auditoria(request, filtro, action,
                                        customgetattr(filtro, nombre_para_audit),
                                        qs_anterior=qs_anterior)
                        messages.success(request, "{} eliminado".format(customgetattr(filtro, nombre_para_audit)))
                    else:
                        messages.error(request, "No tienes permisos para eliminar {}".format(data["titulo"]))
                    return redirect(redirectAfterPostGet(request))
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
        addData(request, data)
        if 'action' in request.GET:
            data["action"] = action = request.GET['action']
            if action == 'add':
                if can_add:
                    data["form"] = Formulario()
                    return render(request, 'area_geografica/pais/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para agregar {}".format(data["titulo"]))
                    return redirect(redirectAfterPostGet(request))
            elif action == 'change':
                if can_change:
                    pk = int(request.GET['pk'])
                    pais = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = Formulario(instance=pais)
                    return render(request, 'area_geografica/pais/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para modificar {}".format(data["titulo"]))
                    return redirect(redirectAfterPostGet(request))
            elif action == 'ver':
                if can_view:
                    pk = int(request.GET['pk'])
                    pais = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = Formulario(instance=pais, ver=True)
                    return render(request, 'area_geografica/pais/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para ver {}".format(data["titulo"]))
                    return redirect(redirectAfterPostGet(request))
        if can_view:
            criterio, filtros, url_vars = request.GET.get('criterio', '').strip(), Q(status=True), ''
            if criterio:
                filtros = filtros & Q(nombre__icontains=criterio)
                data["criterio"] = criterio
                url_vars += '&criterio=' + criterio
            listado = model.objects.filter(filtros)
            data["list_count"] = listado.count()
            data["url_vars"] = url_vars
            paginador(request, listado, 20, data, url_vars)
            return render(request, 'area_geografica/pais/listado.html', data)
        else:
            messages.error(request, "No tienes permisos para ver {}".format(data["titulo"]))
            return redirect('/')