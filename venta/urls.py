from django.urls import path, re_path, include

from .view_pedido import pedidoView

venta_urls = (
    {
        "nombre": "Pagos Online",
        "url": 'pedidos/',
        "vista": pedidoView
    },
)

urlpatterns = [
]

for u in venta_urls:
    urlpatterns.append(re_path(r'^{}$'.format(u["url"]), u["vista"]))
