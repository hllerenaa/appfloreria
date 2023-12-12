from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from core.funciones import addData, paginador
from mantenimiento.models import Carousel, Producto
from seguridad.models import *


def catalogoView(request):
    data = {
        'titulo': 'Catálogo',
        'ruta': request.path,
        'fecha': datetime.now(),
    }
    addData(request, data)

    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        if 'action' in request.GET:
            data["action"] = action = request.GET['action']
            if action == 'ver':
                try:
                    slug = request.GET['id']
                    data['producto'] = producto = Producto.objects.get(slug=slug)
                    return render(request, 'sitio/producto.html', data)
                except Exception as ex:
                    return redirect(request.path)


    criterio, filtros, url_vars = request.GET.get('criterio', '').strip(), Q(status=True), ''
    if criterio:
        filtros = filtros & (Q(nombre__icontains=criterio))
        data["criterio"] = criterio
        url_vars += '&criterio=' + criterio
    listado = Producto.objects.filter(filtros).order_by('orden')
    data["list_count"] = listado.count()
    data["url_vars"] = url_vars
    paginador(request, listado, 9, data, url_vars)
    data['listaRecientes'] = Producto.objects.filter(status=True).order_by('?')[:3]
    return render(request, 'sitio/catalogo.html', data)
