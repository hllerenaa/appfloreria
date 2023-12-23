from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template

from core.custom_models import FormError
from core.funciones import addData, paginador, salva_auditoria, secure_module, redirectAfterPostGet
from .forms import ProductoForm, ItemsAdicionalesForm
from .models import Producto, ProductoItems
from django.contrib import messages
from core.funciones_adicionales import salva_logs, customgetattr
import sys


@login_required
@secure_module
def productoView(request):
    data = {
        'titulo': 'Producto',
        'modulo': 'Mantenimientos',
        'ruta': request.path,
        'fecha': str(date.today())
    }
    addData(request, data)
    model = Producto
    form = ProductoForm
    nombre_para_audit = '__str__'
    nombre_app, nombre_model = model._meta.app_label, model._meta.model_name
    data["can_add"] = can_add = True
    data["can_change"] = can_change = True
    data["can_delete"] = can_delete = True
    data["can_view"] = can_view = True

    if request.method == 'POST':
        res_json = []
        data['action'] = action = request.POST['action']
        try:
            with transaction.atomic():
                if action == 'add':
                    formulario = form(request.POST, request.FILES)
                    if formulario.is_valid():
                        formulario.save()
                        salva_auditoria(request, formulario.instance, action,
                                        customgetattr(formulario.instance, nombre_para_audit),
                                        qs_nuevo=list(model.objects.filter(id=formulario.instance.id).values()))
                        messages.success(request,
                                         "{} agregado".format(customgetattr(formulario.instance, nombre_para_audit)))
                        res_json.append({'error': False,
                                         "to": redirectAfterPostGet(request)
                                         })
                    else:
                        raise FormError(form)
                elif action == 'change':
                    pk = int(request.POST['pk'])
                    qs_anterior = model.objects.filter(pk=pk)
                    instance = qs_anterior.first()
                    qs_anterior = list(qs_anterior.values())
                    formulario = form(request.POST, request.FILES, instance=instance)
                    if formulario.is_valid() and instance:
                        formulario.save()
                        salva_auditoria(request, formulario.instance, action,
                                        customgetattr(formulario.instance, nombre_para_audit),
                                        qs_anterior=qs_anterior,
                                        qs_nuevo=list(model.objects.filter(id=formulario.instance.id).values()))
                        messages.success(request,
                                         "{} agregado".format(customgetattr(formulario.instance, nombre_para_audit)))
                        res_json.append({'error': False,
                                         "to": redirectAfterPostGet(request)
                                         })
                    else:
                        raise FormError(form)
                elif action == 'delete':
                    pk = int(request.POST['id'])
                    qs_anterior = model.objects.filter(pk=pk)
                    instance = qs_anterior.first()
                    qs_anterior = list(qs_anterior.values())
                    instance.status = False
                    instance.save()
                    salva_auditoria(request, instance, action, customgetattr(instance, nombre_para_audit),
                                    qs_anterior=qs_anterior)
                    messages.success(request, f"Registro Eliminado")
                    res_json = {"error": False}
                elif action == 'additem':
                    if can_add:
                        cab = model.objects.get(pk=int(request.POST['id']))
                        form = ItemsAdicionalesForm(request.POST, request.FILES)
                        if form.is_valid():
                            form.instance.producto = cab
                            form.save()
                            salva_auditoria(request, form.instance, action,
                                            customgetattr(form.instance, nombre_para_audit),
                                            qs_nuevo=list(model.objects.filter(id=form.instance.id).values()))
                            messages.success(request,
                                             "{} agregado".format(customgetattr(form.instance, nombre_para_audit)))
                            res_json.append({'error': False,
                                             "to": f"{request.path}?action=itemsadicionales&id={cab.id}"
                                             })
                        else:
                            raise FormError(form)
                    else:
                        res_json.append({"error": True, "message": "You do not have permissions for this action"})
                elif action == 'changeitem':
                    if can_change:
                        qs_anterior = ProductoItems.objects.filter(pk=int(request.POST['id']))
                        filtro = qs_anterior.first()
                        qs_anterior = list(qs_anterior.values())
                        form = ItemsAdicionalesForm(request.POST, request.FILES, instance=filtro)
                        if form.is_valid() and filtro:
                            form.save()
                            salva_auditoria(request, form.instance, action,
                                            customgetattr(form.instance, nombre_para_audit),
                                            qs_anterior=qs_anterior,
                                            qs_nuevo=list(model.objects.filter(id=form.instance.id).values()))
                            messages.success(request,
                                             "{} agregado".format(customgetattr(form.instance, nombre_para_audit)))
                            res_json.append({'error': False,
                                             "to": f"{request.path}?action=itemsadicionales&id={form.instance.producto.id}"
                                             })
                        else:
                            raise FormError(form)
                    else:
                        res_json.append({"error": True, "message": "You do not have permissions for this action"})
                elif action == 'delitem':
                    if can_delete:
                        qs_anterior = ProductoItems.objects.filter(pk=int(request.POST['id']))
                        filtro = qs_anterior.first()
                        qs_anterior = list(qs_anterior.values())
                        filtro.status = False
                        filtro.save()
                        salva_auditoria(request, filtro, action, customgetattr(filtro, nombre_para_audit), qs_anterior=qs_anterior)
                        messages.success(request, f"Record Deleted")
                        res_json = {"error": False}
                    else:
                        messages.error(request, "You don't have permissions to delete {}".format(data['titulo']))
                        res_json = {'error': True, "message": "You don't have permissions to delete {}".format(data['titulo'])}
                return JsonResponse(res_json, safe=False)
        except ValueError as ex:
            res_json.append({'error': True, "message": str(ex)})
        except FormError as ex:
            res_json.append(ex.dict_error)
        except Exception as ex:
            res_json.append({'error': True, "message": f"Intente Nuevamente: {ex}"})

    elif request.method == 'GET':
        if 'action' in request.GET:
            data['action'] = action = request.GET['action']
            if action == 'add':
                data['form'] = form
                return render(request, 'mantenimiento/productos/form.html', data)
            elif action == 'change':
                pk = int(request.GET['id'])
                producto = model.objects.get(pk=pk)
                data['pk'] = pk
                data['form'] = form(instance=producto)
                return render(request,'mantenimiento/productos/form.html', data)
            elif action == 'itemsadicionales':
                try:
                    data['id'] = id = int(request.GET['id'])
                    data['filtro'] = filtro = model.objects.get(pk=id)
                    data['titulo'] = f"Items de {filtro.__str__()}"
                    data['listado'] = listado = filtro.productoitems_set.filter(status=True).order_by('orden')
                    return render(request, 'mantenimiento/productos/itemsadicionales.html', data)
                except Exception as ex:
                    pass
            elif action == 'viewficha':
                try:
                    data['id'] = id = int(request.GET['id'])
                    data['producto'] = filtro = model.objects.get(pk=id)
                    data['titulo'] = f"Items de {filtro.__str__()}"
                    data['listado'] = listado = filtro.productoitems_set.filter(status=True).order_by('orden')
                    template = get_template("mantenimiento/productos/modal/fichaproducto.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass
                    pass
            elif action == 'viewitems':
                try:
                    data['id'] = id = int(request.GET['id'])
                    data['filtro'] = filtro = model.objects.get(pk=id)
                    data['titulo'] = f"Items de {filtro.__str__()}"
                    data['listado'] = listado = filtro.productoitems_set.filter(status=True).order_by('orden')
                    template = get_template("mantenimiento/productos/modal/itemsadicionales.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass
            elif action == 'additem':
                try:
                    data['id'] = id = int(request.GET['id'])
                    data['filtro'] = filtro = model.objects.get(pk=id)
                    form = ItemsAdicionalesForm()
                    numitems = ProductoItems.objects.values('id').filter(status=True, producto=filtro).count() + 1
                    # form.fields['nombre'].initial = f"Item {numitems}"
                    form.fields['orden'].initial = numitems
                    data['form'] = form
                    template = get_template("mantenimiento/productos/modal/form.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass
            elif action == 'changeitem':
                try:
                    data['id'] = id = int(request.GET['id'])
                    data['filtro'] = filtro = ProductoItems.objects.get(pk=id)
                    form = ItemsAdicionalesForm(instance=filtro)
                    data['form'] = form
                    template = get_template("mantenimiento/productos/modal/form.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass

        criterio, filtros, url_vars = request.GET.get('criterio', '').strip(), Q(status=True), ''
        if criterio:
            filtros = filtros & (Q(nombre__icontains=criterio))
            data["criterio"] = criterio
            url_vars += '&criterio=' + criterio
        listado = Producto.objects.filter(filtros)
        data["list_count"] = listado.count()
        data["url_vars"] = url_vars
        paginador(request, listado, 20, data, url_vars)
        return render(request, 'mantenimiento/productos/listado.html',data)
