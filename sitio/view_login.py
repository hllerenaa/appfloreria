import base64
from django.contrib import messages
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from core.correos_background import enviar_correo_html
from core.funciones import addData, ip_client_address, get_decrypt, datetime
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.timezone import activate
from appfloreria import settings
from appfloreria.settings import EMAIL_HOST_USER, URL_GENERAL
from mantenimiento.models import *
from autenticacion.models import Usuario
from seguridad.models import SessionUser

activate(settings.TIME_ZONE)


def login_tienda(request):
    data = {'titulo': 'Iniciar Sesión',}
    addData(request, data)
    if request.method == 'GET':
        des, data['next'] = get_decrypt(request.GET.get('next'))
        if not des:
            data['next'] = request.GET.get('next')
        if request.user.username != "":
            return redirect('/')
        return render(request, 'sitio/seguridad/login.html', data)
    datos = {'resp': False}
    try:
        addData(request, data)
        if request.method == 'POST':
            usuario_, password = request.POST['usuario'], request.POST['password']
            if Usuario.objects.filter(username=usuario_).exists():
                user = authenticate(username=usuario_, password=password)
                if user is not None:
                    if user.is_active:
                        # if user.es_cliente():
                        #     if not user.get_perfil_cli().validado:
                        #         datos['error'] = 'Cuenta pendiente de validación, contactar con los administradores del sitio.'
                        #         return JsonResponse(datos)
                        login(request, user)
                        su = SessionUser.nuevo(request)
                        if user.get_perfil_cli():
                            request.session['perfilprincipal'] = user.get_perfil_cli()
                        datos['resp'] = True
                        if request.POST.get('next'):
                            datos['redirect'] = request.POST.get('next')
                    else:
                        datos['error'] = 'Este usuario a sido desvinculado del sistema'
                else:
                    datos['error'] = 'Credenciales Incorrectas'
            else:
                datos['error'] = 'Usuario no existe'
            return JsonResponse(datos)
    except Exception as ex:
        datos['error'] = 'Credenciales Incorrectas'
        messages.error(request, ex)
        return JsonResponse(datos)


def logout_tienda(request):
    logout(request)
    return redirect('/')
