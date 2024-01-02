from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import Value
from django.db.models.functions import Concat
from core.custom_models import ModelFormBase
from seguridad.models import Configuracion, Modulo, ModuloGrupo, GroupModulo


class ConfiguracionForm(ModelFormBase):
    class Meta:
        model = Configuracion
        exclude = ('paypal_modo', 'payphone_modo', 'porcentaje_pagoonline', 'usuario_creacion', 'terminosycondiciones', 'privacidad', 'faq', 'fondo_perfil', 'banner_login', )

    def __init__(self, *args, **kwargs):
        super(ConfiguracionForm, self).__init__(*args, **kwargs)
        self.fields["ico"].widget.attrs['data-default-file'] = self.instance.ico.url if self.instance.ico else ""
        self.fields["logo_sistema"].widget.attrs['data-default-file'] = self.instance.logo_sistema.url if self.instance.logo_sistema else ""
        self.fields["logo_sistema_white"].widget.attrs['data-default-file'] = self.instance.logo_sistema_white.url if self.instance.logo_sistema_white else ""
        self.fields["fondoprincipal"].widget.attrs['data-default-file'] = self.instance.fondoprincipal.url if self.instance.fondoprincipal else ""
        self.fields['ico'].widget.attrs['data-allowed-file-extensions'] = "jpg jpeg png tiff svg jfif ico"
        self.fields['logo_sistema'].widget.attrs['data-allowed-file-extensions'] = "jpg jpeg png tiff svg jfif ico"
        self.fields['logo_sistema_white'].widget.attrs['data-allowed-file-extensions'] = "jpg jpeg png tiff svg jfif ico"
        self.fields['fondoprincipal'].widget.attrs['data-allowed-file-extensions'] = "jpg jpeg png tiff svg jfif ico"

        for k, v in self.fields.items():

            # if k in ('keymoodle',):
            #     self.fields[k].widget.attrs['col'] = "12"
            # else:
            self.fields[k].widget.attrs['col'] = "6"
            if k in ('telefono', 'telefono_emergencia'):
                self.fields[k].widget.attrs['pattern'] = "\d*"
                self.fields[k].widget.attrs['title'] = "Sólo números"
                self.fields[k].widget.attrs['onKeyPress'] = "return soloNumeros(event)"
                self.fields[k].widget.attrs['pattern'] = "\d*"
            if k in ('valor_mensual', 'valor_anual'):
                self.fields[k].widget.attrs['title'] = "Sólo números"
                self.fields[k].widget.attrs['onKeyPress'] = "return soloNumeros1(event)"


class ModuloForm(ModelFormBase):
    class Meta:
        model = Modulo
        exclude = ('usuario_creacion', 'fecha_registro', 'status')


class GroupForm(ModelFormBase):
    class Meta:
        model = Group
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['permissions'].queryset = self.fields['permissions'].queryset.\
            annotate(full_name_db=Concat('content_type__app_label', Value('__'), 'content_type__model')).\
            exclude(full_name_db__in=['sessions__session', 'auth__permission', 'contenttypes__contenttype',
                                     'admin__logentry', 'authtoken__token', 'seguridad__usuarioconectado', 'seguridad__carousel', 'seguridad__redsocial', 'seguridad__errorlog', 'seguridad__audiusuariotabla',
                                     'background_task__completedtask', 'background_task__task', 'webpush__subscriptioninfo',
                                      'webpush__pushinformation', 'webpush__group', 'authtoken__tokenproxy', 'ventas__pedidodetalle',
                                      'autenticacion__codigo', 'seguridad__usuarionotificacion', 'seguridad__sessionuser']).\
            exclude(content_type__app_label__in=("dobra", "reportes"))


class ModuloGrupoForm(ModelFormBase):
    class Meta:
        model = ModuloGrupo
        exclude = ('usuario_creacion', 'fecha_registro', 'status')

    def __init__(self, *args, **kwargs):
        kwargs["no_requeridos"] = ["modulos"]
        super(ModuloGrupoForm, self).__init__(*args, **kwargs)
        self.fields['modulos'].queryset = self.fields['modulos'].queryset.order_by('orden')
        self.fields['modulos'].widget = forms.HiddenInput()
        self.initial["modulos"] = ""


class GroupModuloForm(ModelFormBase):
    class Meta:
        model = GroupModulo
        exclude = ('usuario_creacion', 'fecha_registro', 'status')

    def __init__(self, *args, **kwargs):
        kwargs["no_requeridos"] = ["modulos"]
        super(GroupModuloForm, self).__init__(*args, **kwargs)
        self.fields['modulos'].queryset = self.fields['modulos'].queryset.order_by('orden')
        self.fields["group"].widget = forms.HiddenInput()


class ConfiguracionTerminosForm(ModelFormBase):
    class Meta:
        model = Configuracion
        fields = ('terminosycondiciones',)

    def __init__(self, *args, **kwargs):
        super(ConfiguracionTerminosForm, self).__init__(*args, **kwargs)


class ConfiguracionPrivacidadForm(ModelFormBase):
    class Meta:
        model = Configuracion
        fields = ('privacidad',)

    def __init__(self, *args, **kwargs):
        super(ConfiguracionPrivacidadForm, self).__init__(*args, **kwargs)


class ConfiguracionFaqForm(ModelFormBase):
    class Meta:
        model = Configuracion
        fields = ('faq',)

    def __init__(self, *args, **kwargs):
        super(ConfiguracionFaqForm, self).__init__(*args, **kwargs)


class ConfiguracionMetodosDePagoForm(ModelFormBase):
    class Meta:
        model = Configuracion
        fields = ('porcentaje_pagoonline', 'payphone_modo', 'paypal_modo')

    def __init__(self, *args, **kwargs):
        super(ConfiguracionMetodosDePagoForm, self).__init__(*args, **kwargs)

        for k, v in self.fields.items():
            self.fields[k].widget.attrs['col'] = "4"
