from django.apps import AppConfig
#from django.db.models.signals import post_save


class MantenimientoConfig(AppConfig):
    name = 'mantenimiento'
    verbose_name = "Mantenimiento o Registros varios"

    # def ready(self):
    #     from mantenimiento.models import Cliente
    #     from mantenimiento.signals import create_cliente
    #     post_save.connect(create_cliente, sender=Cliente)