from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from core.funciones import addData, paginador, salva_auditoria, secure_module
from .forms import CouriersForm
from .models import Couriers
from django.contrib import messages
from core.funciones_adicionales import salva_logs, customgetattr
import sys


@login_required
@secure_module
def couriersView(request):
    data = {'titulo': 'Couriers',
            'modulo': 'Mantenimientos',
            'ruta': request.path,

            }
    model = Couriers
    Formulario = CouriersForm
    nombre_para_audit = '__str__'
    nombre_app, nombre_model = model._meta.app_label, model._meta.model_name
    data["can_add"] = can_add = request.user.has_perm('{}.add_{}'.format(nombre_app, nombre_model))
    data["can_change"] = can_change = request.user.has_perm('{}.change_{}'.format(nombre_app, nombre_model))
    data["can_delete"] = can_delete = request.user.has_perm('{}.delete_{}'.format(nombre_app, nombre_model))
    data["can_view"] = can_view = request.user.has_perm('{}.view_{}'.format(nombre_app, nombre_model))
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
                                             "to": request.path
                                             })
                        else:
                            res_json.append({'error': True,
                                             "form": [{k: v[0]} for k, v in form.errors.items()],
                                             "message": "Error en el formulario"
                                             })
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
                                             "to": request.path
                                             })
                        else:
                            res_json.append({'error': True,
                                             "form": [{k: v[0]} for k, v in form.errors.items()],
                                             "message": "Error en el formulario"
                                             })
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
                    return redirect(request.path)
        except ValueError as ex:
            res_json.append({'error': True,
                             "message": str(ex)
                             })
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
                    return render(request, 'mantenimiento/currier/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para agregar {}".format(data["titulo"]))
                    return redirect(request.path)
            elif action == 'change':
                if can_change:
                    pk = int(request.GET['pk'])
                    instancia = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = Formulario(instance=instancia)
                    return render(request, 'mantenimiento/currier/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para modificar {}".format(data["titulo"]))
                    return redirect(request.path)
            elif action == 'ver':
                if can_view:
                    pk = int(request.GET['pk'])
                    instancia = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = Formulario(instance=instancia, ver=True)
                    return render(request, 'mantenimiento/currier/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para ver {}".format(data["titulo"]))
                    return redirect(request.path)
        if can_view:
            criterio, filtros, url_vars = request.GET.get('criterio', ''), Q(status=True), ''
            if criterio:
                filtros = filtros & (Q(nombre__icontains=criterio))
                data["criterio"] = criterio
                url_vars += '&criterio=' + criterio
            listado = model.objects.filter(filtros)
            data["url_vars"] = url_vars
            paginador(request, listado, 10, data)
            return render(request, 'mantenimiento/currier/listado.html', data)
        else:
            messages.error(request, "No tienes permisos para ver {}".format(data["titulo"]))
            return redirect('/')