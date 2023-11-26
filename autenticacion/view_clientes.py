import sys
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect

from area_geografica.models import Provincia, Ciudad
from core.custom_models import FormError
from core.funciones import addData, paginador, salva_auditoria, secure_module, redirectAfterPostGet, codnombre
from core.funciones_adicionales import salva_logs
from .forms import UserForm, ClienteForm
from django.contrib import messages

from .models import Usuario, PerfilAdministrativo, PerfilCliente


@login_required
@secure_module
def clientesView(request):
    data = {
        'titulo': 'Clientes',
        'modulo': 'Autenticación',
        'ruta': request.path,
        'fecha': str(date.today()),
    }
    addData(request, data)
    model = Usuario
    Formulario = ClienteForm
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
                            if 'ciudad' in request.POST:
                                form.instance.ciudad_id = request.POST['ciudad']
                            username_ = codnombre(request.POST['first_name'], request.POST['last_name'])
                            form.instance.username = username_
                            form.instance.set_password(request.POST["documento"])
                            form.instance.passmoodle = form.instance.set_password_moodle(request.POST["documento"])
                            obj = form.save()
                            perfil_ = PerfilCliente(usuario_id=form.instance.id)
                            perfil_.save()
                            salva_auditoria(request, obj, action,
                                            obj.username + "-" + obj.get_full_name(),
                                            qs_nuevo=list(model.objects.filter(id=obj.id).values()))
                            messages.success(request, "Agregado correctamente.")
                            res_json.append({'error': False,
                                             "to": redirectAfterPostGet(request)
                                             })
                        else:
                            raise FormError(form)
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'change':
                    if can_change:
                        user = model.objects.get(pk=int(request.POST['pk']))
                        qs_anterior = list(model.objects.filter(id=user.id).values())
                        form = Formulario(request.POST, request.FILES, instance=user)
                        if form.is_valid():
                            if 'ciudad' in request.POST:
                                form.instance.ciudad_id = request.POST['ciudad']
                            form.save()
                            if form.instance.get_perfil_cli():
                                perfil_ = PerfilCliente.objects.get(id=form.instance.get_perfil_cli().id)
                            else:
                                perfil_ = PerfilCliente(usuario=form.instance)
                            perfil_.save()
                            salva_auditoria(request, form.instance, action,
                                            form.instance.username + "-" + form.instance.get_full_name(),
                                            qs_anterior=qs_anterior,
                                            qs_nuevo=list(model.objects.filter(pk=form.instance.id).values()))
                            messages.success(request, "Modificado correctamente.")
                            res_json.append({'error': False,
                                             "to": redirectAfterPostGet(request)
                                             })
                        else:
                            raise FormError(form)
                    else:
                        res_json.append({"error": True, "message": "No tienes permisos para esta acción"})
                elif action == 'crearperfiladm':
                    if can_change:
                        user = model.objects.get(pk=int(request.POST['id']))
                        if not user.es_administrativo():
                            perfil_ = PerfilAdministrativo(usuario=user)
                            perfil_.save()
                            salva_auditoria(request, user, action, f'Creo perfil administrativo {user.get_full_name()}')
                            messages.success(request, "Perfil administrativo habilitado.")
                        else:
                            messages.error(request, "Usuario ya cuenta con perfil administrativo")
                    else:
                        messages.error(request, "No tienes permisos para eliminar usuarios")
                    return redirect(redirectAfterPostGet(request))
                elif action == 'crearusuariomoodle':
                    if can_change:
                        user = model.objects.get(pk=int(request.POST['id']))
                        if not user.idusermoodle:
                            user.crear_usuario_moodle()
                            salva_auditoria(request, user, action, f'Creo usuario en moodle {user.get_full_name()}')
                            messages.success(request, "Usuario moodle habilitado.")
                        else:
                            messages.error(request, "Usuario ya cuenta con perfil en moodle")
                    else:
                        messages.error(request, "No tienes permisos para eliminar usuarios")
                    return redirect(redirectAfterPostGet(request))
                elif action == 'delete':
                    if can_delete:
                        user = model.objects.get(pk=int(request.POST['id']))
                        qs_anterior = list(model.objects.filter(id=user.id).values())
                        user.is_active = False
                        user.status = False
                        user.save()
                        salva_auditoria(request, user, action,
                                        user.username + "-" + user.get_full_name(),
                                        qs_anterior=qs_anterior)
                        messages.success(request, "Inhabilitado correctamente.")
                    else:
                        messages.error(request, "No tienes permisos para eliminar usuarios")
                    return redirect(redirectAfterPostGet(request))
                elif action == 'activate':
                    if can_change:
                        user = model.objects.get(pk=int(request.POST['id']))
                        user.is_active = True
                        user.status = True
                        user.save()
                        salva_auditoria(request, user, action,
                                        user.username + "-" + user.get_full_name())
                        messages.success(request, "Habilitado correctamente.")
                    else:
                        messages.error(request, "No tienes permisos para eliminar usuarios")
                    return redirect(redirectAfterPostGet(request))
                elif action == 'change_password':
                    if can_change:
                        user = model.objects.get(pk=int(request.POST['pk']))
                        user.set_password(request.POST["password"])
                        user.passmoodle = user.set_password_moodle(request.POST["password"])
                        user.save()
                        salva_auditoria(request, user, action,
                                        user.username + "-" + user.get_full_name())
                        messages.success(request, "Contraseña del usuario {} / {} cambiada".format(user.get_full_name(),
                                                                                                   user.username))
                    else:
                        messages.error(request, "No tienes permisos para cambiar contraseñas")
                    return redirect(redirectAfterPostGet(request))
                elif action == 'eliminar_foto':
                    if can_delete:
                        user = model.objects.get(pk=int(request.POST['pk']))
                        user.foto = ""
                        user.save()
                        salva_auditoria(request, user, action,
                                        user.username + "-" + user.get_full_name())
                        return JsonResponse({'state': True})
                    else:
                        return JsonResponse({'state': False,
                                             "message": "No tiene permisos para esta acción"
                                             })
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
                    form = Formulario()
                    form.fields['provincia'].queryset = Provincia.objects.none()
                    form.fields['ciudad'].queryset = Ciudad.objects.none()
                    data["form"] = form
                    return render(request, 'autenticacion/usuario/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para agregar usuarios")
                    return redirect(redirectAfterPostGet(request))
            elif action == 'change':
                if can_change:
                    pk = int(request.GET['pk'])
                    user = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["object"] = user
                    form = Formulario(instance=user)
                    if user.ciudad:
                        form.fields['provincia'].queryset = Provincia.objects.filter(status=True, id=user.ciudad.provincia.id)
                        form.fields['ciudad'].queryset = Ciudad.objects.filter(status=True, id=user.ciudad.id)
                    else:
                        form.fields['provincia'].queryset = Provincia.objects.none()
                        form.fields['ciudad'].queryset = Ciudad.objects.none()
                    data["form"] = form
                    return render(request, 'autenticacion/clientes/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para modificar usuarios")
                    return redirect(redirectAfterPostGet(request))
            elif action == 'ver':
                if can_view:
                    pk = int(request.GET['pk'])
                    user = model.objects.get(pk=pk)
                    data["pk"] = pk
                    data["object"] = user
                    data["form"] = Formulario(instance=user, ver=True)
                    return render(request, 'autenticacion/clientes/form.html', data)
                else:
                    messages.error(request, "No tienes permisos para ver usuarios")
                    return redirect(redirectAfterPostGet(request))
        if can_view:
            criterio, filtros, url_vars = request.GET.get('criterio', '').strip(), Q(id__gt=0), ''
            if criterio:
                filtros = filtros & (Q(username__icontains=criterio) | Q(first_name__icontains=criterio) |
                                     Q(last_name__icontains=criterio) | Q(documento__icontains=criterio))
                data["criterio"] = criterio
                url_vars += '&criterio=' + criterio
            listado = model.objects.filter(filtros).filter(perfilcliente__isnull=False, status=True).order_by('-id')
            data["url_vars"] = url_vars
            data["list_count"] = listado.count()
            paginador(request, listado, 20, data, url_vars)
            return render(request, 'autenticacion/clientes/listado.html', data)
        else:
            messages.error(request, "No tienes permisos para ver usuarios")
            return redirect('/')
