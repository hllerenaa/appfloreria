import re
from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import Q

from area_geografica.models import Pais, Ciudad, Provincia
from autenticacion.models import Usuario, PerfilCliente
from core.custom_models import ModelFormBase
from venta.models import Pedido


class RegistroClientePassForm(ModelFormBase):
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    class Meta:
        model = Usuario
        fields = ('email', 'password', 'tipo_documento', 'documento', 'first_name', 'last_name', 'ciudad', 'telefono')

    def __init__(self, *args, **kwargs):
        kwargs['requeridos'] = ('email', 'password', 'tipo_documento', 'documento', 'first_name', 'last_name', 'ciudad',  'telefono')
        kwargs['no_select2'] = ('ciudad',)
        if len(args) == 0:
            kwargs['querysets'] = {
                "ciudad": Ciudad.objects.none()
            }
        super(RegistroClientePassForm, self).__init__(*args, **kwargs)

        for k, v in self.fields.items():
            if k in ('ciudad'):
                self.fields[k].widget.attrs['col'] = "12"
            else:
                self.fields[k].widget.attrs['col'] = "6"

        if self.editando:
            usuario = Usuario.objects.get(id=self.instance.id)
            if usuario.ciudad:
                self.prefijoCelular = usuario.ciudad.provincia.pais.codigotelefono or ""

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        return re.sub("\s+", " ", first_name.strip())

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        return re.sub("\s+", " ", last_name.strip())

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        id = self.instance.id if self.instance else 0
        if Usuario.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exclude(id=id).exists():
            raise ValidationError("Ya existe un usuario con este correo electrónico")
        return email

    def save(self, **kwargs):
        user = super(RegistroClientePassForm, self).save()
        if not self.editando:
            user.set_password(self.cleaned_data["password"])
            user.save()
        if not user.username:
            user.username = self.cleaned_data['email']
        user.save()
        PerfilCliente.objects.get_or_create(usuario_id=user.id)
        return user


class RegistroClienteForm(ModelFormBase):

    class Meta:
        model = Usuario
        fields = ('email', 'tipo_documento', 'documento', 'first_name', 'last_name', 'ciudad', 'telefono')
        labels = {
            "ciudad": "Ubicación"
        }

    def __init__(self, *args, **kwargs):
        kwargs['requeridos'] = ('email', 'tipo_documento', 'documento', 'first_name', 'last_name', 'ciudad', 'telefono')
        kwargs['no_select2'] = ('ciudad',)
        if len(args) == 0:
            kwargs['querysets'] = {
                "ciudad": Ciudad.objects.none()
            }
        super(RegistroClienteForm, self).__init__(*args, **kwargs)

        for k, v in self.fields.items():
            if k in ('email',):
                self.fields[k].widget.attrs['col'] = "12"
            else:
                self.fields[k].widget.attrs['col'] = "6"

        if self.editando:
            usuario = Usuario.objects.get(id=self.instance.id)
            if usuario.ciudad:
                self.prefijoCelular = usuario.ciudad.provincia.pais.codigotelefono or ""

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        return re.sub("\s+", " ", first_name.strip())

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        return re.sub("\s+", " ", last_name.strip())

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        id = self.instance.id if self.instance else 0
        if Usuario.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exclude(id=id).exists():
            raise ValidationError("Ya existe un usuario con este correo electrónico")
        return email

    def save(self, **kwargs):
        user = super(RegistroClienteForm, self).save()
        if not self.editando:
            user.set_password(self.cleaned_data["documento"])
            user.save()
        if not user.username:
            user.username = self.cleaned_data['documento']
        user.cambio_clave = False
        user.save()
        PerfilCliente.objects.get_or_create(usuario_id=user.id)
        return user


class PedidoArchivoPagoForm(ModelFormBase):
    class Meta:
        model = Pedido
        fields = ('entidad_fin', 'archivo_pago',)

    def __init__(self, *args, **kwargs):
        super(PedidoArchivoPagoForm, self).__init__(*args, **kwargs)
        self.fields["archivo_pago"].required = True
        self.fields["entidad_fin"].required = True