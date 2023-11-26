import sys
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.custom_models import FormError
from core.funciones import addData, paginador, salva_auditoria, secure_module, redirectAfterPostGet
from core.funciones_adicionales import ordenar_modulos_url, salva_logs
from seguridad.forms import ModuloForm
from seguridad.models import Modulo, ModuloGrupo
from django.contrib import messages


@login_required
@secure_module
def modulo(request):
    data = {
        'titulo': 'Url',
        'modulo': 'Url',
        'ruta': request.path,
        'fecha': str(date.today())
    }
    addData(request, data)
    model = Modulo
    Formulario = ModuloForm
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
                                            form.instance.nombre,
                                            qs_nuevo=list(model.objects.filter(id=form.instance.id).values()))
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
                        modulo = qs_anterior.first()
                        qs_anterior = list(qs_anterior.values())
                        form = Formulario(request.POST, instance=modulo)
                        if form.is_valid():
                            form.save()
                            salva_auditoria(request, form.instance, action,
                                            form.instance.nombre,
                                            qs_anterior=qs_anterior,
                                            qs_nuevo=list(model.objects.filter(id=form.instance.id).values()))
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
                        modulo = qs_anterior.first()
                        qs_anterior = list(qs_anterior.values())
                        modulo.status = False
                        modulo.save()
                        salva_auditoria(request, modulo, action,
                                        modulo.nombre,
                                        qs_anterior=qs_anterior)
                    else:
                        messages.error(request, "No tienes permisos para eliminar módulos")
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
        if 'action' in request.GET:
            data["action"] = action = request.GET['action']
            if action == 'add':
                if can_add:
                    data["form"] = Formulario()
                    return render(request, 'seguridad/modulo/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para agregar módulos")
                    return redirect(request.path)
            elif action == 'change':
                if can_change:
                    pk = int(request.GET['pk'])
                    modulo = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = Formulario(instance=modulo)
                    return render(request, 'seguridad/modulo/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para modificar módulos")
                    return redirect(request.path)
            elif action == 'ver':
                if can_view:
                    pk = int(request.GET['pk'])
                    modulo = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = Formulario(instance=modulo, ver=True)
                    return render(request, 'seguridad/modulo/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para ver módulos")
                    return redirect(request.path)
        if can_view:
            modulo_grupo, criterio, filtros, url_vars = [int(x) for x in
                                                         request.GET.getlist('modulo_grupo', [])], request.GET.get(
                'criterio', '').strip(), Q(status=True), ''
            if criterio:
                filtros = filtros & Q(nombre__icontains=criterio)
                data["criterio"] = criterio
                url_vars += '&criterio=' + criterio
            if modulo_grupo:
                filtros = filtros & Q(id__in=list(
                    ModuloGrupo.objects.filter(pk__in=modulo_grupo, status=True).values_list('modulos__id',
                                                                                             flat=True).distinct()))
                data["modulo_grupo"] = modulo_grupo
                url_vars += '&' + '&'.join(["modulo_grupo=" + str(x) for x in modulo_grupo])
            modulos = model.objects.filter(filtros)
            data["list_modulo_grupo"] = list_modulo_grupo = ModuloGrupo.objects.filter(status=True)
            data["url_vars"] = url_vars
            ordenar_modulos_url(data, modulos)
            return render(request, 'seguridad/modulo/listado.html', data)
        else:
            messages.error(request, "No tienes permisos para ver módulos")
            return redirect('/')
