from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from autenticacion.models import Usuario, PerfilCliente, PerfilAdministrativo

admin.site.register(Usuario, UserAdmin)
admin.site.register(PerfilCliente)
admin.site.register(PerfilAdministrativo)