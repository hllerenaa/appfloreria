import asyncio

from core.correos_background import enviar_correo_html
from core.email_config import send_html_mail, conectar_cuenta
from core.funciones import addData, salva_auditoria
from appfloreria import settings
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
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
        pass
    elif request.method == 'GET':
        return render(request, 'sitio/carrito/carrito.html', data)
