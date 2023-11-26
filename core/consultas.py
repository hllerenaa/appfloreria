import json
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect
from area_geografica.models import *
from django.http import JsonResponse, HttpResponse


def consultas(request):
    if request.method == 'GET':
        if 'action' in request.GET:
            action = request.GET['action']
            try:
                if action == 'paises':
                    try:
                        lista = []
                        pais = Pais.objects.filter(status=True).order_by('nombre')
                        for p in pais:
                            lista.append([p.id, p.nombre])
                        return JsonResponse({'result': 'ok', 'lista': lista})
                    except Exception as ex:
                        return JsonResponse({"result": "bad", "mensaje": u"Error al obtener los datos."})

                if action == 'provincias':
                    try:
                        pais = Pais.objects.get(pk=request.GET['id'])
                        lista = []
                        for provincia in pais.provincia_set.filter(status=True).order_by('nombre'):
                            lista.append([provincia.id, provincia.nombre])
                        return JsonResponse({'result': 'ok', 'lista': lista})
                    except Exception as ex:
                        return JsonResponse({"result": "bad", "mensaje": u"Error al obtener los datos."})

                if action == 'cantones':
                    try:
                        provincia = Provincia.objects.get(pk=request.GET['id'])
                        lista = []
                        for canton in provincia.ciudad_set.filter(status=True).order_by('nombre'):
                            lista.append([canton.id, canton.nombre])
                        return JsonResponse({'result': 'ok', 'lista': lista})
                    except Exception as ex:
                        return JsonResponse({"result": "bad", "mensaje": u"Error al obtener los datos."})

                if action == 'parroquias':
                    try:
                        canton = Ciudad.objects.get(pk=request.GET['id'])
                        lista = []
                        for parroquia in canton.parroquia_set.filter(status=True).order_by('nombre'):
                            lista.append([parroquia.id, parroquia.nombre])
                        return JsonResponse({'result': 'ok', 'lista': lista})
                    except Exception as ex:
                        return JsonResponse({"result": "bad", "mensaje": u"Error al obtener los datos."})

                if action == 'buscarlocalidad':
                    try:
                        q = request.GET['q'].upper().strip().replace(',', ' ').replace('-',' ').strip()
                        s = q.split()
                        qsubicacion = []
                        if len(s) == 1:
                            qsubicacion = Ciudad.objects.filter(status=True).filter(Q(nombre__icontains=q) | Q(provincia__nombre__icontains=q) | Q(provincia__pais__nombre__icontains=q)).distinct().order_by('nombre')[:50]
                        elif len(s) == 2:
                            qsubicacion = Ciudad.objects.filter(status=True).filter((Q(nombre__icontains=s[0]) & Q(nombre__icontains=s[1])) | (Q(provincia__nombre__icontains=s[1]) | Q(provincia__pais__nombre__icontains=s[1]))).distinct().order_by('nombre')[:50]
                        elif len(s) == 3:
                            qsubicacion = Ciudad.objects.filter(status=True).filter((Q(nombre__icontains=s[0]) & Q(nombre__icontains=s[1])) | (Q(provincia__nombre__icontains=s[1]) & Q(provincia__nombre__icontains=s[2])) | Q(provincia__pais__nombre__icontains=s[2])).distinct().order_by('nombre')[:50]
                        data = {"result": "ok", "results": [{"id": x.id, "name": x.nombre, "provincia": x.provincia.nombre, "pais": x.provincia.pais.nombre , 'prefijo': x.provincia.pais.codigotelefono} for x in qsubicacion]}
                        return JsonResponse(data)
                    except Exception as ex:
                        pass

            except Exception as ex:
                return JsonResponse({"result": "bad", "mensaje": f"Error al obtener los datos. {ex}"})
