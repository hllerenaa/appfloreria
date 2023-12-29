import json
from datetime import date, datetime, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction, models
from django.db.models import Q, Min, Max, Subquery, OuterRef, Count, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.utils import timezone

from appfloreria.settings import GMAP_API_KEY
from area_geografica.models import Pais, Provincia, Ciudad
from autenticacion.models import Usuario
from core.custom_models import FormError
from core.decoradores import custom_atomic_request
from core.email_config import send_html_mail
from core.funciones import addData, mi_paginador, get_decrypt, get_client_ip, get_encrypt, redirectAfterPostGet
from django.contrib import messages
from mantenimiento.models import *
from appfloreria import settings
from seguridad.models import SessionUser
from sitio.forms import RegistroClienteForm, RegistroClientePassForm
from venta.models import Pedido, PedidoDetalle, PedidoAdicionalesDetalle


@custom_atomic_request
def checkoutView(request):
    data = {
        'titulo': 'Confirmación de Pedido',
        'modulo': 'Compra',
        'ruta': request.path,
    }
    addData(request, data)
    if not 'dict_orden' in request.session:
        messages.success(request, f"Debe confirmar su pedido primero para proceder al pago")
        return redirect('/carrito/')
    if request.method == 'POST':
        res_json = []
        action = request.POST.get('action')

        if action == 'crear_pedido':
            form = RegistroClientePassForm(request.POST, instance=request.user if request.user.is_authenticated else None)
            if request.user.is_authenticated:
                form = RegistroClienteForm(request.POST, instance=request.user if request.user.is_authenticated else None)
            if form.is_valid():
                user: Usuario = form.save()
                if not request.user.is_authenticated:
                    datos = {
                        'sucursal': request.config.nombre_empresa,
                        'instancia': user,
                        'pass': request.POST['password'],
                        'url': f'{data["DOMINIO_DEL_SISTEMA"]}',
                        'correo': str(settings.EMAIL_HOST_USER)
                    }
                    subject = f'¡Registro Completo!'
                    to = user.email
                    send_html_mail(subject, "email/registro_usuario.html", datos, [to], [], [])
                    login(request, user)
                    su = SessionUser.nuevo(request)
                orden = request.session['dict_orden']
                total_ = orden['total']
                if request.POST['metodo_pago'] == 'TRANSFERENCIA_BANCARIA':
                    total_ = orden['subtotal_aplicable'] + orden['impuesto_ubicacion']
                pedido = Pedido.objects.create(
                    user_id=user.id,
                    festimada=orden["dateatt"],
                    metodo_pago=request.POST['metodo_pago'],
                    observacion=request.POST.get('notas_pedido'),
                    estado="GUARDADO",
                    fecha_expira=timezone.now() + relativedelta(days=2),
                    latitud=orden['latitud'],
                    longitud=orden['longitud'],
                    address1=orden['add1'],
                    address2=orden['add2'],
                    city=orden['city'],
                    state=orden['state'],
                    zipcode=orden['zipcode'],
                    reference=orden['reference'],
                    km_totales=orden['km_totales'],
                    km_adicionales=orden['km_adicionales'],
                    subtotal=orden['subtotal_aplicable'],
                    impuestos_ubicacion=orden['impuesto_ubicacion'],
                    impuestos=orden['impuesto_pago_online'] if not request.POST[
                                                                       'metodo_pago'] == 'TRANSFERENCIA_BANCARIA' else 0,
                    total=total_,
                    tiempo_de_viaje_en_minutos=request.POST['driving_time']
                )

                pedido.save()

                lista_pedido = request.session['carrito']
                for item in lista_pedido:
                    list_items = item['adicionales']
                    producto = Producto.objects.get(id=item['id'])
                    det = PedidoDetalle.objects.create(
                        item_id=producto.id,
                        pedido_id=pedido.id,
                        cantidad=item['cantidad'],
                        precio=producto.precio,
                        total=item['subtotal']
                    )
                    for adicional in list_items:
                        itemadd = ProductoItems.objects.get(id=adicional['id'])
                        pd = PedidoAdicionalesDetalle.objects.create(item=det, items_adicionales=itemadd, total=itemadd.precio)

                res_json.append(
                    {
                        "error": False,
                        "to": "/pay/{}/".format(get_encrypt(pedido.id)[1])
                    }
                )
            else:
                raise FormError(form)

        return JsonResponse(res_json, safe=False)
    if request.method == 'GET':
        if 'action' in request.GET:
            data["action"] = action = request.GET["action"]
        form = RegistroClienteForm()
        if request.user.is_authenticated:
            form = RegistroClienteForm(instance=request.user)
        data['form'] = form
        from geopy.distance import geodesic
        data['orden'] = orden = request.session['dict_orden']
        you = (str(orden['latitud']) + "," + str(orden['longitud']))
        data['kms'] = kms = float(geodesic((str(data['confi'].latitud) + "," + str(data['confi'].longitud)), you).kilometers)
        data['start_lat'] = start_lat = str(data['confi'].latitud)
        data['start_lon'] = start_lon = str(data['confi'].longitud)
        data['dest_lat'] = dest_lat = str(orden['latitud'])
        data['dest_lon'] = dest_lon = str(orden['longitud'])
        data['dateatt'] = dateatt = str(orden['dateatt'])
        limite_envio = data['confi'].limite_km_envio
        precio_km_pasado = data['confi'].precio_km_pasado
        precio_impuesto_ubicacion = 0
        km_adicionales = 0
        if Decimal(str(kms)) > limite_envio:
            km_adicionales = Decimal(kms - limite_envio)
            precio_impuesto_ubicacion += Decimal((km_adicionales * Decimal(precio_km_pasado)).quantize(Decimal(10) ** -2))
        data['limite_envio'] = str(limite_envio)
        data['km_adicionales'] = km_adicionales
        request.session['dict_orden']['km_totales'] = kms
        request.session['dict_orden']['km_adicionales'] = km_adicionales
        request.session['dict_orden']['precio_impuesto_ubicacion'] = precio_impuesto_ubicacion

        subtotal = float(request.session['total'])
        subtotal_aplicable = float(request.session['total'])
        data['subtotal'] = round(subtotal, 2)
        data['subtotal_aplicable'] = round(subtotal_aplicable, 2)
        request.session['dict_orden']['subtotal_aplicable'] = round(subtotal_aplicable, 2)
        request.session['dict_orden']['subtotal'] = round(subtotal, 2)
        data['impuesto_ubicacion'] = impuesto_ubicacion = round(float(precio_impuesto_ubicacion),
                                                                2) if precio_impuesto_ubicacion else 0
        request.session['dict_orden']['impuesto_ubicacion'] = impuesto_ubicacion
        data['impuesto_pago_online'] = impuesto_pago_online = round(float(subtotal_aplicable * float((data['confi'].porcentaje_pagoonline / Decimal('100')))), 2) if data['confi'].porcentaje_pagoonline else 0
        request.session['dict_orden']['impuesto_pago_online'] = impuesto_pago_online

        totalsinimpuesto_ = subtotal_aplicable + impuesto_ubicacion
        total_ = subtotal_aplicable + impuesto_pago_online + impuesto_ubicacion
        data['totalsinimpuesto'] = round(totalsinimpuesto_, 2)
        request.session['dict_orden']['totalsinimpuesto'] = round(totalsinimpuesto_, 2)
        data['total'] = round(total_, 2)
        request.session['dict_orden']['total'] = round(total_, 2)

        request.session.modified = True
        data["GMAP_API_KEY"] = GMAP_API_KEY
        return render(request, 'sitio/carrito/checkout.html', data)
