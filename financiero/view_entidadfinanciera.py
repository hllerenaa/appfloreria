from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from core.funciones import addData, mi_paginador, salva_auditoria, secure_module
from core.funciones_adicionales import customgetattr
from .forms import EntidadFinancieraForm
from .models import EntidadFinanciera
from django.contrib import messages
from datetime import date, datetime

@login_required
@secure_module
def entidadFinancieraView(request):
    data = {'titulo': 'Entidad Financiera',
            'modulo': 'Financiero',
            'ruta': request.path,

            }
    model = EntidadFinanciera
    Formulario = EntidadFinancieraForm
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
                        form = Formulario(request.POST, request.FILES)
                        if form.is_valid():
                            form.save()
                            salva_auditoria(request, form.instance, action,
                                            customgetattr(form.instance, nombre_para_audit),
                                            qs_nuevo=list(model.objects.filter(id=form.instance.id).values()))
                            messages.success(request, "{} agregado correctamente.".format(customgetattr(form.instance, nombre_para_audit)))
                            res_json.append({'error': False,
                                             "to": request.path + "?action=add" if '_add' in request.POST else request.path
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
                        form = Formulario(request.POST, request.FILES, instance=filtro)
                        if form.is_valid() and filtro:
                            form.save()
                            salva_auditoria(request, form.instance, action,
                                            customgetattr(form.instance, nombre_para_audit),
                                            qs_anterior=qs_anterior,
                                            qs_nuevo=list(model.objects.filter(id=form.instance.id).values()))
                            messages.success(request, "{} modificado correctamente.".format(
                                customgetattr(form.instance, nombre_para_audit)))
                            res_json.append({'error': False,
                                             "to": request.path + "?action=add" if '_add' in request.POST else request.path
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
                    else:
                        messages.error(request, "No tienes permisos para eliminar {}".format(data["titulo"]))
                    return redirect(request.path)
        except ValueError as ex:
            res_json.append({'error': True,
                             "message": str(ex)
                             })
        except Exception as ex:
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
                    return render(request, 'financiero/entidad_financiera/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para agregar {}".format(data["titulo"]))
                    return redirect(request.path)
            elif action == 'change':
                if can_change:
                    pk = int(request.GET['pk'])
                    instancia = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = Formulario(instance=instancia)
                    return render(request, 'financiero/entidad_financiera/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para modificar {}".format(data["titulo"]))
                    return redirect(request.path)
            elif action == 'ver':
                if can_view:
                    pk = int(request.GET['pk'])
                    instancia = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = Formulario(instance=instancia, ver=True)
                    return render(request, 'financiero/entidad_financiera/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para ver {}".format(data["titulo"]))
                    return redirect(request.path)
        if can_view:
            criterio, filtros, url_vars = request.GET.get('criterio', ''), Q(status=True), ''
            if criterio:
                filtros = filtros & Q(nombre__icontains=criterio)
                data["criterio"] = criterio
                url_vars += '&criterio=' + criterio
            listado = model.objects.filter(filtros)
            data["url_vars"] = url_vars
            mi_paginador(request, listado, 40, data)
            return render(request, 'financiero/entidad_financiera/listado.html', data)
        else:
            messages.error(request, "No tienes permisos para ver {}".format(data["titulo"]))
            return redirect('/')