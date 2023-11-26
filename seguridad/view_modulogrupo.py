import sys
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import CharField, Value as V, Q
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.custom_models import FormError
from core.funciones import addData, paginador, salva_auditoria, merge_values, secure_module, redirectAfterPostGet
from core.funciones_adicionales import ordenar_modulos_url, salva_logs
from seguridad.forms import ModuloGrupoForm
from seguridad.models import ModuloGrupo, Modulo
from django.contrib import messages


@login_required
@secure_module
def modulo_grupo(request):
    data = {
        'titulo': 'Grupos de Url',
        'modulo': 'Grupos de Urls',
        'ruta': request.path,
        'fecha': str(date.today())
    }
    addData(request, data)
    model = ModuloGrupo
    Formulario = ModuloGrupoForm
    nombre_app, nombre_model = model._meta.app_label, model._meta.model_name
    data["can_add"] = can_add = True
    data["can_change"] = can_change = True
    data["can_delete"] = can_delete = True
    data["can_view"] = can_view = True
    if request.method == 'POST':
        res_json = []
        action = request.POST['action']
        try:
            if action == 'add':
                if can_add:
                    form = Formulario(request.POST)
                    if form.is_valid():
                        try:
                            with transaction.atomic():
                                form.save()
                                mod_lista = request.POST.getlist('c_modulos', [])
                                for ml in mod_lista:
                                    datos = eval(ml)
                                    mod = Modulo.objects.filter(url=datos["url"])
                                    if mod.exists():
                                        mod.update(orden=datos["orden"], url=datos["url"])
                                        mod_obj = mod.first()
                                    else:
                                        mod_obj = Modulo.objects.create(orden=datos["orden"], nombre=datos["nombre"],
                                                                        url=datos["url"])
                                    form.instance.modulos.add(mod_obj)
                                salva_auditoria(request, form.instance, action,
                                                form.instance.nombre,
                                                qs_nuevo=list(merge_values(
                                                    ModuloGrupo.objects.filter(id=form.instance.id).values('id',
                                                                                                           'nombre',
                                                                                                           'icono',
                                                                                                           'modulos__nombre',
                                                                                                           'prioridad'))))
                                res_json.append({'error': False,
                                                 "to": redirectAfterPostGet(request)
                                                 })
                        except ValueError as e:
                            res_json.append({'error': True,
                                             "message": str(e)
                                             })
                        except Exception as ex:
                            pass
                    else:
                        raise FormError(form)
                else:
                    res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
            elif action == 'change':
                if can_change:
                    qs_anterior = ModuloGrupo.objects.filter(pk=int(request.POST['pk']))
                    modulo = qs_anterior.first()
                    qs_anterior = list(merge_values(qs_anterior.values('id',
                                                                       'nombre',
                                                                       'icono',
                                                                       'modulos__nombre',
                                                                       'prioridad')))
                    form = Formulario(request.POST, instance=modulo)
                    if form.is_valid():
                        try:
                            with transaction.atomic():
                                form.save()
                                mod_lista = request.POST.getlist('c_modulos', [])
                                for ml in mod_lista:
                                    datos = eval(ml)
                                    mod = Modulo.objects.filter(url=datos["url"])
                                    if mod.exists():
                                        mod.update(orden=datos["orden"], url=datos["url"])
                                        mod_obj = mod.first()
                                    else:
                                        mod_obj = Modulo.objects.create(orden=datos["orden"], nombre=datos["nombre"],
                                                                        url=datos["url"])
                                    form.instance.modulos.add(mod_obj)
                                salva_auditoria(request, form.instance, action,
                                                form.instance.nombre,
                                                qs_anterior=qs_anterior,
                                                qs_nuevo=list(merge_values(
                                                    ModuloGrupo.objects.filter(id=form.instance.id).values('id',
                                                                                                           'nombre',
                                                                                                           'icono',
                                                                                                           'modulos__nombre',
                                                                                                           'prioridad'))))
                                res_json.append({'error': False,
                                                 "to": redirectAfterPostGet(request)
                                                 })
                        except ValueError as e:
                            res_json.append({'error': True,
                                             "message": str(e)
                                             })
                        except Exception as ex:
                            pass
                    else:
                        raise FormError(form)
                else:
                    res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
            elif action == 'delete':
                if can_delete:
                    qs_anterior = ModuloGrupo.objects.filter(pk=int(request.POST['id']))
                    modulo = qs_anterior.first()
                    qs_anterior = list(merge_values(qs_anterior.values('id',
                                                                       'nombre',
                                                                       'icono',
                                                                       'modulos__nombre',
                                                                       'prioridad')))
                    try:
                        with transaction.atomic():
                            modulo.status = False
                            modulo.save()
                            salva_auditoria(request, modulo, action,
                                            modulo.nombre,
                                            qs_anterior=qs_anterior)
                    except ValueError as e:
                        messages.error(request, str(e))
                    except Exception as ex:
                        pass
                else:
                    messages.error(request, "No tienes permisos para eliminar grupos de módulos")
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
                    data["form"] = form = Formulario()
                    qs_modulos = form.fields["modulos"].queryset
                    ordenar_modulos_url(data, qs_modulos)
                    return render(request, 'seguridad/modulogrupo/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para agregar grupos de módulos")
                    return redirect(redirectAfterPostGet(request))
            elif action == 'change':
                if can_change:
                    pk = int(request.GET['pk'])
                    modulo = ModuloGrupo.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = form = Formulario(instance=modulo)
                    qs_modulos = form.fields["modulos"].queryset
                    data["modulos_seleccionados"] = modulos_seleccionados = list(
                        modulo.modulos.all().values_list('url', flat=True))
                    ordenar_modulos_url(data, qs_modulos, modulos_seleccionados)
                    return render(request, 'seguridad/modulogrupo/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para modificar grupos de módulos")
                    return redirect(redirectAfterPostGet(request))
            elif action == 'ver':
                if can_view:
                    pk = int(request.GET['pk'])
                    modulo = ModuloGrupo.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = form = Formulario(instance=modulo, ver=True)
                    qs_modulos = form.fields["modulos"].queryset
                    data["modulos_seleccionados"] = modulos_seleccionados = list(
                        modulo.modulos.all().values_list('url', flat=True))
                    ordenar_modulos_url(data, qs_modulos, modulos_seleccionados)
                    return render(request, 'seguridad/modulogrupo/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para ver grupos de módulos")
                    return redirect(redirectAfterPostGet(request))
            elif action == 'ver_modulos':
                pk = int(request.GET['pk'])
                modulo = ModuloGrupo.objects.get(pk=pk)
                return JsonResponse(list(modulo.modulos.all().order_by('orden').annotate(
                    nombres=Concat('orden', V(', '), 'nombre', V(' ('), 'url', V(')'),
                                   output_field=CharField())).values('nombres')), safe=False)
        if can_view:
            criterio, filtros, url_vars = request.GET.get('criterio', '').strip(), Q(status=True), ''
            if criterio:
                filtros = filtros & Q(nombre__icontains=criterio)
                data["criterio"] = criterio
                url_vars += '&criterio=' + criterio
            modulos = ModuloGrupo.objects.filter(filtros)
            data["url_vars"] = url_vars
            paginador(request, modulos.order_by('prioridad'), 10, data, url_vars)
            return render(request, 'seguridad/modulogrupo/listado.html', data)
        else:
            messages.error(request, "No tienes permisos para ver grupos de módulos")
            return redirect('/')
