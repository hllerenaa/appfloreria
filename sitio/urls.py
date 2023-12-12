from django.conf.urls import url
from django.urls import path

from .index import index
from .view_catalogo import catalogoView
from .view_registro import registro
from .view_login import login_tienda, logout_tienda
from .view_restaurar import restaurar
from .view_recordarusername import recordarusername
from .view_changepass import changepass
from .view_perfil import perfil
from .view_faq import faq
from .view_politicasprivacidad import politicasprivacidad
from .view_terminoscondiciones import terminosycondiciones

urlpatterns = [
    path('', index),
    url(r'^terminosycondiciones/', terminosycondiciones),
    url(r'^privacidad/', politicasprivacidad),
    url(r'^faq/', faq),
    url(r'^perfil/', perfil),
    url(r'^register/', registro),
    url(r'^login/', login_tienda),
    url(r'^logout/', logout_tienda),
    url(r'^restorepass/', restaurar),
    url(r'^restoreusername/', recordarusername),
    url(r'^changepass/', changepass),
    url(r'^catalogo/', catalogoView),
]
