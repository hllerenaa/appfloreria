from django.urls import path, re_path, include
from .view_carrousel import carrouselView
from .view_redessociales import redessocialesView

mantenimiento_urls = (
    {
        "nombre": "Carousel View",
        "url": 'carousel/',
        "vista": carrouselView
    },
    {
        "nombre": "Redes Sociales",
        "url": 'redessociales/',
        "vista": redessocialesView
    },
)

urlpatterns = [
]

for u in mantenimiento_urls:
    urlpatterns.append(re_path(r'^{}$'.format(u["url"]), u["vista"]))
