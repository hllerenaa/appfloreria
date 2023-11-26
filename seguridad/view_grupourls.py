import sys
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import CharField, Value as V
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.custom_models import FormError
from core.funciones import addData, salva_auditoria, merge_values, secure_module
from core.funciones_adicionales import salva_logs
from seguridad.forms import GroupModuloForm
from seguridad.models import ModuloGrupo, GroupModulo
from django.contrib import messages


@login_required
@secure_module
def grupoUrlsView(request, pk, slug_name):
    group = GroupModulo.objects.get(pk=int(pk))
    data = {'titulo': 'Urls para el rol: {}'.format(group.group.name),
            'modulo': 'Urls para el rol: {}'.format(group.group.name),
            'ruta': request.path,
            'fecha': str(date.today()),
            'obj': group,
            "breadcums": [{"url": "/seguridad/grupo/", "nombre": "Roles de Usuario"}],
            }
    addData(request, data)
    model = GroupModulo
    Formulario = GroupModuloForm
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
                        pass
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'change':
                    if can_change:
                        qs_anterior = model.objects.filter(pk=int(request.POST['pk']))
                        instancia = qs_anterior.first()
                        qs_anterior = list(merge_values(qs_anterior.values('id', 'group__name', 'modulos__nombre', 'modulos__url')))
                        form = Formulario(request.POST, instance=instancia)
                        if form.is_valid() and instancia:
                            try:
                                with transaction.atomic():
                                    g = form.save()
                                    g.group_id = group.group.pk
                                    g.save()
                                    salva_auditoria(request, form.instance, action,
                                                    g.group.name,
                                                    qs_anterior=qs_anterior,
                                                    qs_nuevo=list(merge_values(model.objects.filter(id=g.id).values('id', 'group__name', 'modulos__nombre', 'modulos__url'))))
                                    res_json.append({'error': False,
                                                     "to": "/seguridad/grupo/"
                                                     })
                            except ValueError as e:
                                transaction.rollback()
                                res_json.append({'error': True,
                                                 "message": str(e)
                                                 })
                            except Exception as ex:
                                transaction.rollback()
                        else:
                            raise FormError(form)
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'delete':
                    if can_delete:
                        pass
                        # qs_anterior = model.objects.filter(pk=int(request.POST['id']))
                        # instancia = qs_anterior.first()
                        # qs_anterior = list(merge_values(qs_anterior.values('id', 'group__name', 'modulos__nombre', 'modulos__url')))
                        # try:
                        #     with transaction.atomic():
                        #         instancia.status = False
                        #         instancia.save()
                        #         salva_auditoria(request, instancia, action,
                        #                         instancia.nombre,
                        #                         qs_anterior=qs_anterior)
                        # except ValueError as e:
                        #     messages.error(request, str(e))
                        # except Exception as ex:
                        #     pass
                    else:
                        messages.error(request, "No tienes permisos para eliminar urls al rol {}".format(group.group.name))
                    return redirect(request.path)
        except ValueError as ex:
            transaction.rollback()
            res_json.append({'error': True,
                             "message": str(ex)
                             })
        except FormError as ex:
            res_json.append(ex.dict_error)
        except Exception as ex:
            transaction.rollback()
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
                    pass
                    # data["form"] = form = Formulario(initial={"group": pk})
                    # data["qs_modulos"] = qs_modulos = form.fields["modulos"].queryset
                    # return render(request, 'seguridad/grupourls/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para agregar urls al rol {}".format(group.group.name))
                    return redirect(request.path)
            elif action == 'change':
                if can_change:
                    modulo = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = form = Formulario(instance=modulo)
                    qs_modulos = form.fields["modulos"].queryset
                    data["modulos_agrupados"] = ModuloGrupo.objects.filter(status=True)
                    data["modulos_seleccionados"] = modulos_seleccionados = list(modulo.modulos.all().values_list('id', flat=True))
                    return render(request, 'seguridad/grupourls/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para modificar urls al rol {}".format(group.group.name))
                    return redirect(request.path)
            elif action == 'ver':
                if can_view:
                    modulo = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = form = Formulario(instance=modulo, ver=True)
                    qs_modulos = form.fields["modulos"].queryset
                    data["modulos_seleccionados"] = modulos_seleccionados = modulo.modulos.all()
                    return render(request, 'seguridad/grupourls/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para ver urls al rol {}".format(group.group.name))
                    return redirect(request.path)
            elif action == 'ver_modulos':
                modulo = model.objects.get(pk=pk)
                return JsonResponse(list(modulo.modulos.all().order_by('orden').annotate(nombres=Concat('orden', V(', '), 'nombre', V(' ('), 'url', V(')'), output_field=CharField())).values('nombres')), safe=False)
        if can_view:
            pass
            # criterio, filtros, url_vars = request.GET.get('criterio', '').strip(), Q(status=True), ''
            # if criterio:
            #     filtros = filtros & Q(nombre__icontains=criterio)
            #     data["criterio"] = criterio
            #     url_vars += '&criterio=' + criterio
            # modulos = ModuloGrupo.objects.filter(filtros)
            # data["url_vars"] = url_vars
            # paginador(request, modulos.order_by('prioridad'), 10, data)
            # return render(request, 'seguridad/modulogrupo/listado.html', data)
        else:
            messages.error(request, "No tienes permisos para ver urls al rol {}".format(group.group.name))
            return redirect('/')