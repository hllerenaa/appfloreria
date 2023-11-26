"""
   Django 4.1
"""
from django.contrib import admin
from django.urls import path

from area_geografica.urls import area_geografica_urls
from core.funciones import db_table_exists
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.views.static import serve

from autenticacion.urls import autenticacion_urls
from autenticacion.view_perfil import perfilView
from core.ajax import ConsultasAjax
from appfloreria.view_clearsitedata import clearSiteDataView
from mantenimiento.urls import mantenimiento_urls
from appfloreria import settings
from appfloreria.view_redirect import redirectView, redirectToUrlView
from seguridad.models import Configuracion, Modulo
from seguridad.urls import seguridad_urls
from seguridad.view_index import index
from django.conf.urls.static import static
from core.consultas import consultas

confi = Configuracion.get_instancia()
icon_url = confi.ico.url if confi.ico else ""
favicon_view = RedirectView.as_view(url=icon_url, permanent=True)
urls_sistema = (
    {
        "nombre": "Áreas Geográficas",
        "url": "area-geografica/",
        "sub_urls": area_geografica_urls,
        "include": include('area_geografica.urls'),
        "name": None,
        "vista": None
    },
    {
        "nombre": "Autenticación",
        "url": 'autenticacion/',
        "sub_urls": autenticacion_urls,
        "include": include('autenticacion.urls'),
        "name": None,
        "vista": None
    },
    {
        "nombre": "Seguridad",
        "url": 'seguridad/',
        "sub_urls": seguridad_urls,
        "include": include('seguridad.urls'),
        "name": None,
        "vista": None
    },
    {
        "nombre": "Mantenimientos",
        "url": 'mantenimiento/',
        "sub_urls": mantenimiento_urls,
        "include": include('mantenimiento.urls'),
        "name": None,
        "vista": None
    },
    # {
    #     "nombre": "Reportes",
    #     "url": 'reporte/',
    #     "sub_urls": reporte_urls,
    #     "include": include('reporte.urls'),
    #     "name": None,
    #     "vista": None
    # }
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel/', index),
    path('perfilpanel/', perfilView),
    path('consultas/', consultas, name='Consultas API'),
    path('ajaxrequest/', ConsultasAjax.as_view(), name='Ajax Consultas v1'),
    path('ajaxrequest/<slug:accion>', ConsultasAjax.as_view(), name='Ajax Consultas v1'),
    path('ajaxrequest/<slug:accion>/<str:pk>', ConsultasAjax.as_view(), name='Ajax Consultas v1'),
    path('redirect-to-url/<int:pk>/', redirectToUrlView),
    # urls apache
    re_path(r'^favicon\.ico', favicon_view),
    path('clear-site-data/', clearSiteDataView),
    # select2
    path("select2/", include("django_select2.urls")),
    path('', include('sitio.urls')),
    #webpush
    path('webpush/', include('webpush.urls')),
    # pwa
    path('', include('pwa.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
                    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}), ]

for u in urls_sistema:
    if u["vista"] and not u["include"]:
        if u["name"]:
            urlpatterns.append(path('{}'.format(u["url"]), u["vista"], name=u["name"]))
        else:
            urlpatterns.append(path('{}'.format(u["url"]), u["vista"]))
    elif not u["vista"] and u["include"]:
        if u["name"]:
            urlpatterns.append(path('{}'.format(u["url"]), u["include"], name=u["name"]))
        else:
            urlpatterns.append(path('{}'.format(u["url"]), u["include"]))

if db_table_exists(Modulo._meta.db_table):
    qs_modulos = Modulo.objects.filter(status=True)
    for u in urls_sistema:
        url = "/{}".format(u["url"])
        modulos = qs_modulos.filter(url__startswith=url)
        if u["sub_urls"]:
            for su in u["sub_urls"]:
                mod_url = "/{}{}".format(u["url"], su["url"])
                # if modulos.filter(url=mod_url).exists():
                #     mod = modulos.filter(url=mod_url).first()
                #     if mod.nombre != su["nombre"]:
                #         mod.nombre = su["nombre"]
                #         mod.save()

admin.site.site_header = "{} {}".format("Administración", "appfloreria")
admin.site.site_title = "{} {}".format("Administración", "appfloreria")
