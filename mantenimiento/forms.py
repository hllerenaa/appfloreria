from django import forms
from area_geografica.models import Provincia
from core.custom_models import ModelFormBase
from core.validadores import es_cedula, es_ruc, es_pasaporte
from django.core.exceptions import ValidationError
from mantenimiento.models import *


class CouriersForm(ModelFormBase):
    class Meta:
        model = Couriers
        exclude = ('usuario_creacion', 'fecha_registro', 'hora_registro', 'status')

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        if self.editando and Couriers.objects.filter(status=True, nombre__iexact=nombre).exclude(id=self.instance.id).exists():
            raise ValidationError("Ya existe un Couriers con este nombre")
        elif not self.editando and Couriers.objects.filter(status=True, nombre__iexact=nombre).exists():
            raise ValidationError("Ya existe un Couriers con este nombre")
        return nombre


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


class ProductoForm(ModelFormBase):
    class Meta:
        model = Producto
        exclude = ('usuario_creacion','fecha_registro', 'hora_registro', 'status', 'slug',)

    def __init__(self, *args, **kwargs):
        ver = kwargs.pop('ver') if 'ver' in kwargs else False
        instancia = kwargs["instance"] if 'instance' in kwargs else None
        super(ProductoForm, self).__init__(*args, **kwargs)
        for k, v in self.fields.items():
            if k in ('foto1', 'foto2', 'foto3', 'foto4', ):
                self.fields[k].widget.attrs['col'] = "6"
            if k in ('orden', 'nombre', 'precio'):
                self.fields[k].widget.attrs['col'] = "4"
            if k in ('descripcion', 'activo'):
                self.fields[k].widget.attrs['col'] = "12"


class ItemsAdicionalesForm(ModelFormBase):
    class Meta:
        model = ProductoItems
        exclude = ('usuario_creacion','fecha_registro', 'hora_registro', 'status', 'producto',)

    def __init__(self, *args, **kwargs):
        ver = kwargs.pop('ver') if 'ver' in kwargs else False
        instancia = kwargs["instance"] if 'instance' in kwargs else None
        super(ItemsAdicionalesForm, self).__init__(*args, **kwargs)
        for k, v in self.fields.items():
            self.fields[k].widget.attrs['col'] = "6"