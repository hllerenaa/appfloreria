from django.conf.urls import url

from financiero.view_cuentafinanciera import cuentaFinancieraView
from financiero.view_entidadfinanciera import entidadFinancieraView
# from financiero.view_pagos import pagosAprobadosView
# from financiero.view_pedidospendientes import pedidosPendientesView
# from transaccion.view_pedidospendientes import pedidosPendientesView
# from transaccion.view_pagosprocesados import pagosProcesadosView

financiero_urls = (
    {
        "nombre": "Entidad Financiera",
        "url": 'entidad-financiera/',
        "vista": entidadFinancieraView,
    },
    {
        "nombre": "Cuentas Financieras",
        "url": 'cuentas-financieras/',
        "vista": cuentaFinancieraView,
    },
    # {
    #     "nombre": "Pagos Pendientes",
    #     "url": 'pagos-pendientes/',
    #     "vista": pedidosPendientesView,
    # },
    # {
    #     "nombre": "Pagos Procesados",
    #     "url": 'pagos-procesados/',
    #     "vista": pagosProcesadosView,
    # },
    # {
    #     "nombre": "Pagos Pendientes",
    #     "url": 'pagos-pendientes/',
    #     "vista": pedidosPendientesView,
    # },
    # {
    #     "nombre": "Pagos Aprobados",
    #     "url": 'pagos-aprobados/',
    #     "vista": pagosAprobadosView,
    # },
)

urlpatterns = [

]

for u in financiero_urls:
    urlpatterns.append(url(r'^{}$'.format(u["url"]), u["vista"]))
