import sys
from datetime import datetime
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q
from core.custom_models import ModeloBase
from core.funciones_adicionales import remover_espacios_de_mas
from core.models_utils import FileNameUploadToPath
from core.validadores import solo_numeros, validate_file_size_2mb
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as trad
from hashlib import md5


class Usuario(AbstractUser, ModeloBase):
    TIPO_DOCUMENTO = (
        ("CEDULA", "Cédula"),
        ("RUC", "RUC"),
        ("PASAPORTE", "Pasaporte"),
        ("NINGUNO", "Ninguno"),
    )
    SEXO = (
        ("MASCULINO", "Masculino"),
        ("FEMENINO", "Femenino"),
        ("NINGUNO", "Sin definir"),
    )
    email = models.EmailField(trad('email address'), unique=False)
    foto = models.FileField(upload_to=FileNameUploadToPath('fotousuario/', "foto_perfil", ["username"]), max_length=600,  blank=True, null=True, verbose_name="Foto", validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'tiff', "jfif", "svg"]), validate_file_size_2mb])
    sexo = models.CharField(verbose_name="Sexo", max_length=50, choices=SEXO, null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True, verbose_name='Teléfonos', validators=[solo_numeros])
    tipo_documento = models.CharField(verbose_name="Tipo Documento", max_length=50, choices=TIPO_DOCUMENTO, default="NINGUNO")
    documento = models.CharField(max_length=20, null=True, blank=True, verbose_name='Cédula/RUC/Pasaporte', validators=[solo_numeros])
    ciudad = models.ForeignKey('area_geografica.Ciudad', on_delete=models.PROTECT, blank=True, null=True, verbose_name='Ciudad')
    cambio_clave = models.BooleanField(default=False, verbose_name='Cambio de Contraseña Obligatorio')

    def set_password_moodle(self, pwd):
        self.passmoodle = md5(pwd.encode("utf-8")).hexdigest()
        return self.passmoodle

    def check_password_moodle(self, pwd):
        return self.passmoodle == md5(pwd.encode("utf-8")).hexdigest()

    # TIPO_DOCUMENTO
    CEDULA = "CEDULA"
    RUC = "RUC"
    PASAPORTE = "PASAPORTE"

    # @staticmethod
    # def pais_choices_searchs():
    #     return ['nombre__icontains']

    # @staticmethod
    # def provincia_choices_searchs():
    #     return ['nombre__icontains']
    #
    # @staticmethod
    # def provincia_dependent_fields():
    #     return {'pais': 'pais'}
    #
    # @staticmethod
    # def ciudad_choices_searchs():
    #     return ['nombre__icontains']
    #     # return ['nombre__icontains', 'provincia__nombre__icontains', 'provincia__pais__nombre__icontains']

    @staticmethod
    def ciudad_dependent_fields():
        return {'provincia__pais': 'pais', 'provincia': 'provincia'}

    def primernombre(self):
        return self.first_name.split()[0].lower().capitalize()

    def get_nombre(self):
        return "{} - {}".format(self.username, self.get_full_name().title(), self.documento if self else "")

    def usuario_activo(self):
        if self.is_active:
            return "fas fa-check-circle text-success"
        else:
            return "fas fa-times-circle text-danger"

    def groups_str(self):
        return ", ".join(list(self.groups.all().values_list('name', flat=True)))

    def nombre_corto(self):
        import re
        fn = re.sub("\s+", " ", self.first_name.strip()).split(" ")
        ln = re.sub("\s+", " ", self.last_name.strip()).split(" ")
        return "{} {}".format(fn[0], ln[0]).title()

    def get_foto(self):
        if self.foto:
            return self.foto.url
        else:
            return "/static/foto_defaultd.png"
        # try:
        #     import requests
        #     from appfloreria.settings import MEDIA_ROOT
        #     import os
        #     letra1 = (self.first_name[0] if len(self.first_name) > 0 else "").upper()
        #     letra2 = (self.last_name[0] if len(self.last_name) > 0 else "").upper()
        #     filename = "{}{}_LETTERAVATAR.png".format(letra1, letra2)
        #     if not os.path.exists(os.path.join(MEDIA_ROOT, filename)):
        #         r = requests.get(
        #             "https://ui-avatars.com/api/?bold=true&background=2e52a9&color=ffe600&name={}+{}".format(letra1, letra2),
        #             allow_redirects=True)
        #         open(os.path.join(MEDIA_ROOT, filename), 'wb').write(r.content)
        #     return "/media/{}".format(filename)
        # except Exception as ex:
        #     pass

    def datos(self):
        return "{} {}".format(self.first_name, self.last_name).title()

    def save(self, *args, **kwargs):
        self.first_name = remover_espacios_de_mas(self.first_name).title()
        self.last_name = remover_espacios_de_mas(self.last_name).title()
        super(Usuario, self).save(*args, **kwargs)

    def es_administrativo(self):
        return self.perfiladministrativo_set.filter(status=True).exists()

    def es_cliente(self):
        return self.perfilcliente_set.filter(status=True).exists()

    def get_perfil_adm(self):
        return self.perfiladministrativo_set.filter(status=True).first()

    def get_perfil_cli(self):
        return self.perfilcliente_set.filter(status=True).first()

    def __str__(self):
        return "{} {} {}".format(self.documento, self.last_name, self.first_name).title()

    def telefono_formateado(self):
        if self.ciudad:
            telf = f'+{self.ciudad.provincia.pais.codigotelefono} {self.telefono}'
        else:
            telf = f'{self.telefono}'
        return telf

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = "Perfiles"
        ordering = ('id',)


class PerfilCliente(ModeloBase):
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Usuario')

    def __str__(self):
        return "{}".format(self.usuario.__str__())

    class Meta:
        verbose_name = 'Perfil Cliente'
        verbose_name_plural = 'Perfil Clientes'
        constraints = [
            models.UniqueConstraint(fields=['usuario'],
                                    name='autenticacion_PerfilCliente_usuario_unique',
                                    condition=Q(usuario__isnull=False) & Q(status=True)),
        ]

    def save(self, force_insert=False, force_update=False, using=None, **kwargs):
        super(PerfilCliente, self).save(force_insert, force_update, using)


class PerfilAdministrativo(ModeloBase):
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, verbose_name='Usuario')
    idtelegram = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return "{}".format(self.usuario.__str__())

    class Meta:
        verbose_name = 'Perfil Administrativo'
        verbose_name_plural = 'Perfil Administrativo'

    def save(self, force_insert=False, force_update=False, using=None, **kwargs):
        super(PerfilAdministrativo, self).save(force_insert, force_update, using)