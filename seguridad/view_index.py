from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import get_template

from django.db.models import Value, Count, Sum, F, FloatField
from django.db.models.functions import Coalesce
from autenticacion.models import PerfilCliente
from core.funciones import addData, secure_module
from sitio.models import VisitaEntorno
from seguridad.models import *


@login_required
@secure_module
def index(request):
    data = {
        'titulo': 'Inicio',
        'modulo': 'Menu',
        'ruta': '/',
        'fecha': datetime.now(),
    }
    addData(request, data)

    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        if 'action' in request.GET:
            data["action"] = action = request.GET['action']
            if action == 'consultarContectados':
                try:
                    data["conectados"] = conectados = UsuarioConectado.objects.filter(sesion__expire_date__gt=timezone.now()).distinct('user').exclude(sesion__session_key=request.session.session_key)
                    usuarios = Usuario.objects.filter(is_active=True, status=True).order_by('username').exclude(id__in=list(conectados.values_list('user_id', flat=True)))
                    data["usuarios"] = usuarios.exclude(id=request.user.pk)
                    data["conectados"] = conectados.exclude(user_id=request.user.pk)
                    template = get_template('usuarios_online.html')
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    return JsonResponse({"result": False, 'mensaje': ex})

        rangofechas = []
        rangofechasstr = []
        fechadesde = datetime.now().date() - timedelta(days=15)
        fechahasta = datetime.now().date()
        for day in range((fechahasta - fechadesde).days + 1):
            fechafiltro = fechadesde + timedelta(days=day)
            rangofechas.append("{} {}".format((fechadesde + timedelta(days=day)).strftime("%d"), (fechadesde + timedelta(days=day)).strftime("%b")))
            rangofechasstr.append(str(fechafiltro))
        visita = VisitaEntorno.objects.filter(fecha_visita__gte=fechadesde).values('fecha_visita').annotate(total=Coalesce(Count('fecha_visita'), 0)).values_list('total', 'fecha_visita')
        data['rangofechas'] = rangofechas
        data['rangofechasstr'] = rangofechasstr
        data['ultimasvisitas'] = visita
        data['totalvisitas'] = totaltodos = VisitaEntorno.objects.filter(fecha_visita__gte=fechadesde).count()
        maxvisitasday = max(VisitaEntorno.objects.filter(fecha_visita__gte=fechadesde).values('fecha_visita').annotate(total=Coalesce(Count('fecha_visita'), 0)).values_list('total', flat=True))
        if maxvisitasday <= 5:
            maxvisitasday = 10
        data['maxvisitaday'] = maxvisitasday

        return render(request, 'seguridad/index.html', data)
