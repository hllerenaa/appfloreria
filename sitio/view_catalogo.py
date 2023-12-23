from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from core.funciones import addData, paginador
from mantenimiento.models import Carousel, Producto, ProductoItems
from seguridad.models import *


def catalogoView(request):
    data = {
        'titulo': 'Catálogo',
        'ruta': request.path,
        'fecha': datetime.now(),
    }
    addData(request, data)

    if request.method == 'POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'addcarrito':
                try:
                    producto_id = request.POST['producto_id']
                    producto = Producto.objects.get(id=producto_id)
                    item_ids = request.POST.getlist('additional_items[]')  # IDs de los items adicionales seleccionados
                    # Objeto del carrito en la sesión
                    carrito = request.session.get('carrito', [])
                    # Crear un identificador único para el producto y sus items adicionales
                    identificador_unico = f"{producto_id}-{'-'.join(sorted(item_ids))}"
                    # Verificar si el producto con los mismos items adicionales ya existe en el carrito
                    producto_existente = next(
                        (item for item in carrito if item['identificador_unico'] == identificador_unico), None)
                    if producto_existente:
                        # Si el producto con los mismos items adicionales ya existe, aumentar la cantidad
                        producto_existente['cantidad'] += 1
                    else:
                        # Si el producto no existe, agregarlo al carrito
                        adicionales = [
                            {
                                'id': item_id,
                                'nombre': ProductoItems.objects.get(id=item_id).nombre,
                                'precio': str(ProductoItems.objects.get(id=item_id).precio)
                            } for item_id in item_ids
                        ]
                        precio_total_adicionales = sum(Decimal(item['precio']) for item in adicionales)
                        subtotal = Decimal(producto.precio) + precio_total_adicionales
                        producto_principal = {
                            'identificador_unico': identificador_unico,
                            'id': producto.id,
                            'nombre': producto.nombre,
                            'precio': str(producto.precio),
                            'cantidad': 1,
                            'adicionales': adicionales,
                            'subtotal': str(subtotal)
                        }
                        carrito.append(producto_principal)
                    # Calcular el total del carrito
                    total = sum(Decimal(item['subtotal']) for item in carrito)
                    # Guardar el carrito y el total actualizado en la sesión
                    request.session['carrito'] = carrito
                    request.session['total'] = str(total)
                    request.session.modified = True

                    return JsonResponse({'mensaje': 'Producto agregado al carrito', 'resp': True})
                except Exception as ex:
                    return JsonResponse({'mensaje': 'Intentelo más tarde', 'resp': False})



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
