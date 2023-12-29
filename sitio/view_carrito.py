import asyncio
import json

from django.utils.dateparse import parse_date

from appfloreria.settings import GMAP_API_KEY
from core.correos_background import enviar_correo_html
from core.email_config import send_html_mail, conectar_cuenta
from core.funciones import addData, salva_auditoria
from appfloreria import settings
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.utils.timezone import activate
from mantenimiento.models import *
from autenticacion.models import Usuario

activate(settings.TIME_ZONE)
from django.template.loader import render_to_string
from random import choice
from django.core import mail
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.html import strip_tags
from seguridad.models import *
import time
from django.utils.timezone import activate

@login_required()
def carritoView(request):
    data = {'titulo': 'Carrito de Compras', }
    addData(request, data)
    resp = {'resp': False}
    if request.method == 'POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'delitem':
                try:
                    identificador_unico = request.POST.get('identificador_unico')
                    # Obtener el carrito de la sesión
                    carrito = request.session.get('carrito', [])
                    total = Decimal(request.session.get('total', '0'))
                    # Encontrar y eliminar el producto del carrito
                    carrito = [producto for producto in carrito if producto['identificador_unico'] != identificador_unico]
                    # Recalcular el total
                    total = sum(Decimal(producto['subtotal']) for producto in carrito)
                    # Actualizar el carrito y el total en la sesión
                    request.session['carrito'] = carrito
                    request.session['total'] = str(total)
                    request.session.modified = True
                    return JsonResponse({'mensaje': 'Producto eliminado del carrito', 'resp': True})
                except Exception as ex:
                    return JsonResponse({'mensaje': f'Intentelo más tarde, {ex}', 'resp': False})
            if action == 'saveorder':
                try:
                    dateatt = request.POST['dateatt']
                    add1, add2, zipcode = request.POST['add1'], request.POST['add2'], request.POST['zipcode']
                    latitud, longitud, reference = request.POST['latitud'], request.POST['longitud'], request.POST['reference']
                    city, state = request.POST['city'], request.POST['state']
                    fecha_actual = datetime.now().date()
                    if not parse_date(dateatt) > fecha_actual:
                        raise NameError(f"La fecha de entrega debe ser mayor a la fecha actual")
                    dict_orden = {
                        'detalle': request.session['carrito'],
                        'dateatt': dateatt, 'add1': add1, 'add2': add2,
                        'zipcode': zipcode, 'latitud': latitud,
                        'longitud': longitud, 'reference': reference,
                        'direccion': '{}, {}, {}'.format(add1, add2, reference),
                        'city': city, 'state': state,
                    }
                    request.session['dict_orden'] = dict_orden
                    response = JsonResponse({'resp': True, "to": f"/checkout/"})
                    return HttpResponse(response.content)
                except Exception as ex:
                    response = JsonResponse({'resp': False, "mensaje": f"{ex}"})
                    return HttpResponse(response.content)
    elif request.method == 'GET':
        data["GMAP_API_KEY"] = GMAP_API_KEY
        data["existe_orden"] = 'dict_orden' in request.session
        return render(request, 'sitio/carrito/carrito.html', data)
