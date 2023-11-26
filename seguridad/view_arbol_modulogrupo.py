import json
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from core.funciones import addData, salva_auditoria, secure_module
from seguridad.models import ModuloGrupo, Modulo
from django.contrib import messages


@login_required
@secure_module
def arbol_modulo_grupo(request):
    data = {'titulo': 'Grupos de Urls',
            'modulo': 'Grupos de Urls',
            'ruta': request.path,
            'ruta_val': request.path,
            'group': 'Seguridad',
            'fecha': str(date.today())
            }
    addData(request, data)
    model = ModuloGrupo
    nombre_app, nombre_model = model._meta.app_label, model._meta.model_name
    data['can_add'] = can_add = True
    data['can_change'] = can_change = True
    data['can_delete'] = can_delete = True
    data['can_view'] = can_view = True

    if request.method == 'POST':
        res_json = []
        action = request.POST['action']
        if action == 'cambiar_lugar_grupo':
            if can_change:
                try:
                    with transaction.atomic():
                        c_modulos = request.POST.getlist('c_modulos', [])
                        for x in c_modulos:
                            cm = json.loads(x)
                            cm["pk_origen"] = int(cm["pk_origen"])
                            cm["pk_destino"] = int(cm["pk_destino"])
                            cm["orden"] = int(cm["orden"])
                            if cm["pk_destino"] > 0:
                                mg_origen = ModuloGrupo.objects.get(pk=cm["pk_origen"])
                                mg_destino = ModuloGrupo.objects.get(pk=cm["pk_destino"])
                                modulo = Modulo.objects.get(pk=cm['pk_modulo'])
                                modulo.orden = cm["orden"]
                                modulo.save()
                                mg_origen.modulos.remove(modulo)
                                mg_destino.modulos.add(modulo)
                        messages.success(request, "Grupos de urls cambiados correctamente")
                except ValueError as e:
                    messages.error(request, str(e))
                except Exception as ex:
                    messages.error(request, "Hubo un error, intente nuevamente")
            else:
                messages.error(request, "No tiene permisos para realizar esta acción")
            return redirect(request.path)

    elif request.method == 'GET':
        if can_view:
            modulos = ModuloGrupo.objects.filter(status=True).order_by('prioridad')
            data['listado'] = modulos
            return render(request, 'seguridad/modulogrupo/listado_arbol.html', data)
        else:
            messages.error(request, "No tienes permisos para ver grupos de módulos")
            return redirect('/')