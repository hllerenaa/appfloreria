from django.urls import path, re_path, include

from .view_reportes import reportesView
from .view_pedido import pedidoView

venta_urls = (
    {
        "nombre": "Pagos Online",
        "url": 'pedidos/',
        "vista": pedidoView
    },
    {
        "nombre": "Reporte",
        "url": 'reportes/',
        "vista": reportesView
    },
)

urlpatterns = [
]

for u in venta_urls:
    urlpatterns.append(re_path(r'^{}$'.format(u["url"]), u["vista"]))
