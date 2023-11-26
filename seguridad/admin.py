from django.contrib import admin
from django.utils.safestring import mark_safe

from seguridad.models import ErrorLog, Configuracion, AudiUsuarioTabla, Modulo, GroupModulo, ModuloGrupo


class ErrorLogAdmin(admin.ModelAdmin):
    list_per_page = 15
    search_fields = ('usuario__username', 'usuario__documento',
                     'usuario__first_name', 'usuario__last_name')
    list_display = ('descripcion', 'archivo', 'accion', 'metodo', 'usuario', 'corregido', 'fecha')
    list_filter = ('corregido', 'accion', 'metodo', 'fecha')


    def edit_tag(self, obj):
        return mark_safe(
            f'<a href="{obj.get_absolute_url()}?edit=True">Editar</a>'
        )

    edit_tag.short_description = 'Editar'

admin.site.register(ErrorLog, ErrorLogAdmin)
admin.site.register(Configuracion)
admin.site.register(Modulo)
admin.site.register(GroupModulo)
admin.site.register(ModuloGrupo)

class AudiUsuarioTablaAdmin(admin.ModelAdmin):
    list_per_page = 15
    search_fields = ('usuario__username', 'usuario__documento',
                     'usuario__first_name', 'usuario__last_name', 'accion')
    list_filter = ('accion', 'fecha')

admin.site.register(AudiUsuarioTabla, AudiUsuarioTablaAdmin)
