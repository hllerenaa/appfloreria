import sys
from datetime import date
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.custom_models import FormError
from core.funciones import addData, paginador, salva_auditoria, merge_values, secure_module, redirectAfterPostGet
from core.funciones_adicionales import get_verbose_name, salva_logs, get_app_label
from seguridad.forms import GroupForm
from django.contrib import messages


@login_required
@secure_module
def grupo(request):
    data = {
        'titulo': 'Roles de Usuario',
        'modulo': 'Roles de Usuario',
        'ruta': request.path,
        'fecha': str(date.today())
    }
    addData(request, data)
    model = Group
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
                        form = GroupForm(request.POST)
                        if form.is_valid():
                            g = form.save()
                            salva_auditoria(request, form.instance, action,
                                            form.instance.name,
                                            qs_nuevo=list(merge_values(
                                                Group.objects.filter(id=form.instance.id).values('id', 'name',
                                                                                                 'permissions__name'))))
                            res_json.append({'error': False,
                                             "to": redirectAfterPostGet(request)
                                             })
                        else:
                            raise FormError(form)
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'change':
                    if can_change:
                        qs_anterior = Group.objects.filter(pk=int(request.POST['pk']))
                        group = qs_anterior.first()
                        qs_anterior = list(merge_values(qs_anterior.values('id', 'name', 'permissions__name')))
                        form = GroupForm(request.POST, instance=group)
                        if form.is_valid():
                            g = form.save()
                            salva_auditoria(request, form.instance, action,
                                            form.instance.name,
                                            qs_anterior=qs_anterior,
                                            qs_nuevo=list(merge_values(
                                                Group.objects.filter(id=form.instance.id).values('id', 'name',
                                                                                                 'permissions__name'))))
                            res_json.append({'error': False,
                                             "to": redirectAfterPostGet(request)
                                             })
                        else:
                            raise FormError(form)
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'delete':
                    if can_delete:
                        qs_anterior = Group.objects.filter(pk=int(request.POST['id']))
                        group = qs_anterior.first()
                        qs_anterior = list(merge_values(qs_anterior.values('id', 'name', 'permissions__name')))
                        salva_auditoria(request, group, action,
                                        group.name,
                                        qs_anterior=qs_anterior)
                        group.delete()
                    else:
                        messages.error(request, "No tienes permisos para eliminar grupos")
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
                    data["form"] = form = GroupForm()
                    permisos = []
                    qs_permisos = form.fields["permissions"].queryset
                    appsQs = qs_permisos.values_list('content_type__app_label', flat=True).order_by(
                        'content_type__app_label').distinct()
                    for a in appsQs:
                        appLabel = {
                            "app": a,
                            "modelos": []
                        }
                        for p in qs_permisos.filter(content_type__app_label=a).values('content_type__model',
                                                                                      'content_type__app_label',
                                                                                      'content_type__id',
                                                                                      'full_name_db').order_by(
                            'content_type__model').distinct():
                            # permisos.append({"modelo": p["content_type__model"].title(),
                            #                  "permisos": qs_permisos.filter(content_type_id=p["content_type__id"])})
                            nombreModelo = get_verbose_name(p["content_type__app_label"], p['content_type__model'])
                            nombreModelo = nombreModelo.title() if nombreModelo else p['content_type__model'].title()
                            appLabel["modelos"].append(
                                {"nombre": 'Rol de Usuario' if p["full_name_db"] == 'auth__group' else nombreModelo,
                                 "permisos": qs_permisos.filter(content_type_id=p["content_type__id"])}
                            )
                        appLabel["app"] = get_app_label(appLabel["app"])
                        appLabel["modelos"] = list(sorted(appLabel["modelos"], key=lambda i: i['nombre']))
                        permisos.append(appLabel)
                    permisos = list(sorted(permisos, key=lambda i: i['app']))
                    data["permisos"] = permisos
                    return render(request, 'seguridad/grupo/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para agregar grupos")
                    return redirect(redirectAfterPostGet(request))
            elif action == 'change':
                if can_change:
                    pk = int(request.GET['pk'])
                    group = Group.objects.get(pk=pk)
                    data["pk"] = pk
                    data["form"] = form = GroupForm(instance=group)
                    permisos = []
                    qs_permisos = form.fields["permissions"].queryset
                    appsQs = qs_permisos.values_list('content_type__app_label', flat=True).order_by(
                        'content_type__app_label').distinct()
                    for a in appsQs:
                        appLabel = {
                            "app": a,
                            "modelos": []
                        }
                        for p in qs_permisos.filter(content_type__app_label=a).values('content_type__model',
                                                                                      'content_type__app_label',
                                                                                      'content_type__id',
                                                                                      'full_name_db').order_by(
                            'content_type__model').distinct():
                            # permisos.append({"modelo": p["content_type__model"].title(),
                            #                  "permisos": qs_permisos.filter(content_type_id=p["content_type__id"])})
                            nombreModelo = get_verbose_name(p["content_type__app_label"], p['content_type__model'])
                            nombreModelo = nombreModelo.title() if nombreModelo else p['content_type__model'].title()
                            appLabel["modelos"].append(
                                {"nombre": 'Rol de Usuario' if p["full_name_db"] == 'auth__group' else nombreModelo,
                                 "permisos": qs_permisos.filter(content_type_id=p["content_type__id"])}
                            )
                        appLabel["app"] = get_app_label(appLabel["app"])
                        appLabel["modelos"] = list(sorted(appLabel["modelos"], key=lambda i: i['nombre']))
                        permisos.append(appLabel)
                    permisos = list(sorted(permisos, key=lambda i: i['app']))
                    data["permisos"] = permisos
                    ch_perms = list(group.permissions.all().values_list('id', flat=True))
                    data["ch_perms"] = ch_perms
                    return render(request, 'seguridad/grupo/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para modificar grupos")
                    return redirect(redirectAfterPostGet(request))
            elif action == 'ver':
                if can_view:
                    pk = int(request.GET['pk'])
                    group = Group.objects.get(pk=pk)
                    data["pk"] = pk
                    data["ver"] = True
                    data["form"] = form = GroupForm(instance=group, ver=True)
                    permisos = []
                    qs_permisos = form.fields["permissions"].queryset
                    appsQs = qs_permisos.values_list('content_type__app_label', flat=True).order_by(
                        'content_type__app_label').distinct()
                    for a in appsQs:
                        appLabel = {
                            "app": a,
                            "modelos": []
                        }
                        for p in qs_permisos.filter(content_type__app_label=a).values('content_type__model',
                                                                                      'content_type__app_label',
                                                                                      'content_type__id',
                                                                                      'full_name_db').order_by(
                            'content_type__model').distinct():
                            # permisos.append({"modelo": p["content_type__model"].title(),
                            #                  "permisos": qs_permisos.filter(content_type_id=p["content_type__id"])})
                            nombreModelo = get_verbose_name(p["content_type__app_label"], p['content_type__model'])
                            nombreModelo = nombreModelo.title() if nombreModelo else p['content_type__model'].title()
                            appLabel["modelos"].append(
                                {"nombre": 'Rol de Usuario' if p["full_name_db"] == 'auth__group' else nombreModelo,
                                 "permisos": qs_permisos.filter(content_type_id=p["content_type__id"])}
                            )
                        appLabel["app"] = get_app_label(appLabel["app"])
                        appLabel["modelos"] = list(sorted(appLabel["modelos"], key=lambda i: i['nombre']))
                        permisos.append(appLabel)
                    permisos = list(sorted(permisos, key=lambda i: i['app']))
                    data["permisos"] = permisos
                    ch_perms = list(group.permissions.all().values_list('id', flat=True))
                    data["ch_perms"] = ch_perms
                    return render(request, 'seguridad/grupo/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para ver grupos")
                    return redirect(redirectAfterPostGet(request))
            elif action == 'ver_permisos':
                pk = int(request.GET['pk'])
                group = Group.objects.get(pk=pk)
                lista = []
                pem = group.permissions.all().values('name', 'codename', 'content_type__app_label',
                                                     'content_type__model').order_by('content_type__app_label')
                for p in pem:
                    lista.append({'name': p['content_type__model'],
                                  'codename': p['codename'],
                                  'content_type__app_label': p['content_type__app_label'],
                                  'content_type__model': ' '.join(str(p['name']).lower().replace("can", "Puede") \
                                                                  .replace('add', 'Agregar') \
                                                                  .replace('view', 'Ver') \
                                                                  .replace('delete', 'Eliminar') \
                                                                  .replace('change', 'Modificar').split(' ')[0:2])})
                return JsonResponse(lista, safe=False)

        if can_view:
            criterio, filtros, url_vars = request.GET.get('criterio', '').strip(), Q(id__gt=0), ''
            if criterio:
                filtros = filtros & Q(name__icontains=criterio)
                data["criterio"] = criterio
                url_vars += '&criterio=' + criterio
            grupos = Group.objects.filter(filtros)
            data["url_vars"] = url_vars
            paginador(request, grupos, 10, data, url_vars)
            return render(request, 'seguridad/grupo/listado.html', data)
        else:
            messages.error(request, "No tienes permisos para ver grupos")
            return redirect('/')
