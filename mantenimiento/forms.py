from django import forms
from area_geografica.models import Provincia
from core.custom_models import ModelFormBase
from core.validadores import es_cedula, es_ruc, es_pasaporte
from django.core.exceptions import ValidationError
from mantenimiento.models import *


class CarouselForm(ModelFormBase):
    class Meta:
        model = Carousel
        exclude = ('usuario_creacion', 'fecha_registro', 'hora_registro', 'status')

    def __init__(self, *args, **kwargs):
        ver = kwargs.pop('ver') if 'ver' in kwargs else False
        instancia = kwargs["instance"] if 'instance' in kwargs else None
        super(CarouselForm, self).__init__(*args, **kwargs)
        self.fields['imagen'].widget.attrs['data-default-file'] = instancia.imagen.url if instancia and instancia.imagen else ""
        self.fields['imagen'].widget.attrs['data-allowed-file-extensions'] = "jpg jpeg png tiff svg jfif"
        for k, v in self.fields.items():
            if k in ('imagen', 'orden'):
                self.fields[k].widget.attrs['required'] = "true"


class RedesForm(ModelFormBase):
    class Meta:
        model = RedesSociales
        exclude = ('usuario_creacion', 'fecha_registro', 'hora_registro', 'status')

    def __init__(self, *args, **kwargs):
        ver = kwargs.pop('ver') if 'ver' in kwargs else False
        super(RedesForm, self).__init__(*args, **kwargs)
        for k, v in self.fields.items():
            self.fields[k].widget.attrs['required'] = "true"
            if not k in ('href'):
                self.fields[k].widget.attrs['oninput'] = "mayus(this);"
