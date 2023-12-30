from core.custom_models import ModelFormBase
from mantenimiento.models import Couriers
from venta.models import Pedido


class PedidoForm(ModelFormBase):
    class Meta:
        model = Pedido
        fields = ('couriers', )

    def __init__(self, *args, **kwargs):
        ver = kwargs.pop('ver') if 'ver' in kwargs else False
        instancia = kwargs["instance"] if 'instance' in kwargs else None
        super(PedidoForm, self).__init__(*args, **kwargs)
        self.fields['couriers'].queryset = Couriers.objects.filter(status=True).order_by('agencia')
        for k, v in self.fields.items():
            self.fields[k].widget.attrs['col'] = "12"
            if k in ('couriers',):
                self.fields[k].widget.attrs['class'] = "form-control select2-simple"


class PedidoEnvioForm(ModelFormBase):
    class Meta:
        model = Pedido
        fields = ('estado_entrega', 'fecha_entrega', 'detalle_entrega', 'archivo_entrega')

    def __init__(self, *args, **kwargs):
        ver = kwargs.pop('ver') if 'ver' in kwargs else False
        instancia = kwargs["instance"] if 'instance' in kwargs else None
        super(PedidoEnvioForm, self).__init__(*args, **kwargs)
        for k, v in self.fields.items():
            self.fields[k].widget.attrs['col'] = "12"
            if k in ('estado_entrega',):
                self.fields[k].widget.attrs['required'] = "true"
                self.fields[k].widget.attrs['class'] = "form-control select2-simple"