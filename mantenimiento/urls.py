from django.urls import path, re_path, include
from .view_carrousel import carrouselView
from .view_redessociales import redessocialesView
from .view_producto import productoView

mantenimiento_urls = (
    {
        "nombre": "Carrousel",
        "url": 'carousel/',
        "vista": carrouselView
    },
    {
        "nombre": "Redes Sociales",
        "url": 'redessociales/',
        "vista": redessocialesView
    },
    {
        "nombre": "Producto",
        "url": 'productos/',
        "vista": productoView
    },
)

urlpatterns = [
]

for u in mantenimiento_urls:
    urlpatterns.append(re_path(r'^{}$'.format(u["url"]), u["vista"]))
