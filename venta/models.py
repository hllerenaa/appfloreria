from _decimal import Decimal
from django.core.validators import FileExtensionValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType
from core.funciones_adicionales import customgetattr
from core.models_utils import UserUploadToPath
from core.validadores import validate_file_size_3mb, validate_file_size_20mb
from core.custom_models import ModeloBase
from mantenimiento.models import *
from appfloreria.settings import AUTH_USER_MODEL

ESTADO_PEDIDO = (
    ("GUARDADO", "Guardado (Se registró pero aún no realiza el pago)"),
    ("EN_ESPERA", "En espera de aprobación"),
    ("ANULADO", "Anulado"),
    ("COMPLETADO", "Completado"),
    ("DEVUELTO", "Devuelto",),
    ("ERROR_METODO_PAGO", "Error en el médoto de pago")
)

METODO_PAGOS = (
    ("PAYPHONE", "Payphone"),
    ("PAYPAL", "Paypal"),
    ("TRANSFERENCIA_BANCARIA", "Transferencia Bancaria")
)


def _estado_pedido(self):
    s = ""
    if self.estado == "GUARDADO":
        s = '<i class="text-secondary fas fa-ellipsis-h"></i> Pendiente'
    elif self.estado == "EN_ESPERA":
        s = '<i class="text-warning far fa-clock"></i> Pendiente de aprobación'
    elif self.estado == "ANULADO":
        s = '<i class="text-danger fas fa-times-circle"></i> Anulado'
    elif self.estado == "DEVUELTO":
        s = '<i class="text-danger fas fa-times-circle"></i> Devuelto'
    elif self.estado == "COMPLETADO":
        s = '{} Completado'.format('<i class="text-success fas fa-check-circle"></i>')
    elif self.estado == "ERROR_METODO_PAGO":
        s = '{} Error en el pago'.format('<i class="text-danger fas fa-times-circle"></i>')
    return mark_safe(s)


def funcUser(instance):
    return instance.user


TIPO_ENTORNO = ((True, "Producción"), (False, "Test"),)


class Pedido(ModeloBase):
    ip = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Ip')
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Usuario que hizo el pedido", related_name='+')
    festimada = models.DateField(blank=True, null=True, verbose_name="Fecha de Entrega")
    latitud = models.FloatField(default=0, verbose_name="Latitud. Orden")
    longitud = models.FloatField(default=0, verbose_name="Longitud. Orden")
    address1 = models.TextField("Dirección 1", null=True, blank=True, default='')
    address2 = models.TextField("Dirección 2", null=True, blank=True, default='')
    city = models.TextField("Ciudad", null=True, blank=True, default='')
    state = models.TextField("Provincia", null=True, blank=True, default='')
    zipcode = models.TextField("Zip Code", null=True, blank=True, default='')
    reference = models.TextField("Reference", null=True, blank=True, default='')
    km_totales = models.FloatField(default=0, verbose_name="Total Kilometros")
    km_adicionales = models.FloatField(default=0, verbose_name="Kilometros Adicionalesc")
    observacion = models.TextField("Notas de pedido", null=True, blank=True, default='')
    metodo_pago = models.CharField("Método de pago", max_length=255, choices=METODO_PAGOS)
    subtotal = models.DecimalField(verbose_name="Subtotal", default=0, max_digits=30, decimal_places=2, )
    impuestos_ubicacion = models.DecimalField(verbose_name="Taxes Location", default=0, max_digits=30, decimal_places=2)
    impuestos = models.DecimalField(verbose_name="impuestos", default=0, max_digits=30, decimal_places=2, )
    total = models.DecimalField(verbose_name="Total", default=0, max_digits=30, decimal_places=2, )
    tiempo_de_viaje_en_minutos = models.PositiveIntegerField("Tiempo de viaje en minutos", default=0)
    # DATOS TRANSFERENCIA
    comprobante = models.CharField("Comprobante", max_length=500, null=True, blank=True)
    comprobantejson = models.TextField("Comprobante Json", null=True, blank=True)
    entidad_fin = models.ForeignKey("financiero.CuentaFinancieraEmpresa", on_delete=models.PROTECT, null=True, blank=True)
    archivo_pago = models.FileField(upload_to=UserUploadToPath("pedidos/pagos/", funcUser), validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'tiff', "jfif", "pdf"]), validate_file_size_3mb], null=True, blank=True)
    estado = models.CharField("Estado", max_length=255, choices=ESTADO_PEDIDO)
    fecha_expira = models.DateTimeField("Fecha que expira el pedido. Si no lo completa, se borrará en la fecha establecida.")
    session_user = models.ForeignKey("seguridad.SessionUser", on_delete=models.PROTECT, null=True, blank=True)
    pago_reversado = models.BooleanField("Pago reversado", default=False)
    fecha_reversado = models.DateTimeField("Fecha de pago reversado", null=True, blank=True)
    razon_reverso = models.TextField(default='', blank=True, null=True)
    pago_reversado_por = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Pago reversado por", null=True, blank=True, related_name="venta_pedido_pago_reversado_por")
    modo_pago = models.BooleanField("Ejecución de Paypal", choices=TIPO_ENTORNO, default=1)

    def get_telefono(self):
        return self.user.telefono_formateado()

    def get_nombres(self):
        return self.user.datos()

    def __str__(self):
        return f"{self.id} - {self.user.username} Sub: {self.subtotal}, Imp: {self.impuestos}, Total: {self.total}, Estado: {self.get_estado_display()}"

    @property
    def es_pago_electronico(self):
        return self.metodo_pago in ("PAYPHONE", "PAYPAL")

    def typefile(self):
        if self.archivo_pago:
            return self.archivo_pago.name[self.archivo_pago.name.rfind("."):]
        else:
            return None

    def get_icon(self):
        i = ''
        if self.metodo_pago == "PAYPAL":
            i = '<b><i class="fab fa-paypal" style="color: #2E86C1;"></i></b>'
        elif self.metodo_pago == "TRANSFERENCIA_BANCARIA":
            i = '<i class="fas fa-comments-dollar"></i>'
        elif self.metodo_pago == "PAYPHONE":
            i = '<img src="/static/iconos/payphonelogo.webp" width="20" />'
        return mark_safe(i)

    def get_detalle(self):
        return PedidoDetalle.objects.filter(status=True, pedido=self)

    def estado_pedido(self):
        return _estado_pedido(self)

    def lista_histial(self):
        return HistorialPedido.objects.filter(status=True, pedido__id=self.pk).order_by('-id')

    def get_resp_metodo_pago(self):
        Modelo = PagoTransferencia if self.metodo_pago == "TRANSFERENCIA_BANCARIA" else \
                 PagoPayPhone if self.metodo_pago == "PAYPHONE" else \
                 PagoPayPal if self.metodo_pago == "PAYPAL" else None

        obj = Modelo.objects.filter(
            content_type__id=ContentType.objects.get_for_model(self).id,
            object_id=self.id
        ).first() if Modelo else None

        salida = []

        if obj:
            for x in obj._meta.fields:
                f = x.name
                if not f in ('id', 'status', 'fecha_registro', 'hora_registro', 'content_type', 'object_id', 'modelo', 'paypal_fee', 'final_capture', 'usuario_creacion'):
                    salida.append(
                        {
                            "nombre": obj._meta.get_field(f).verbose_name,
                            "valor": customgetattr(obj, f)
                        }
                    )

        return salida

    class Meta:
        ordering = ("estado", "id")
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        constraints = [
            models.CheckConstraint(check=Q(metodo_pago__in=("PAYPHONE", "TRANSFERENCIA_BANCARIA", "PAYPAL")),
                                   name='venta__Pedido__metodo_pago__in'),
            models.CheckConstraint(check=Q(estado__in=list(x[0] for x in ESTADO_PEDIDO)),
                                   name='venta__Pedido__estado__in'),
        ]


class PedidoDetalle(ModeloBase):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, verbose_name="Cabecera Pedido")
    item = models.ForeignKey("mantenimiento.Producto", on_delete=models.PROTECT, verbose_name="Selected product")
    precio = models.DecimalField(verbose_name="Precio", default=0, max_digits=30, decimal_places=2,)
    cantidad = models.DecimalField(verbose_name="Cantidad", default=1, max_digits=30, decimal_places=0,)
    total = models.DecimalField(verbose_name="Total", default=0, max_digits=30, decimal_places=2,)

    def detalle(self):
        return self.pedidoadicionalesdetalle_set.filter(status=True).order_by('items_adicionales__item__orden')

    def __str__(self):
        return f"{self.item} ({self.precio} x {self.cantidad}) Total: {self.total}"


class PedidoAdicionalesDetalle(ModeloBase):
    item = models.ForeignKey(PedidoDetalle, on_delete=models.PROTECT, verbose_name="Product Detail")
    items_adicionales = models.ForeignKey("mantenimiento.ProductoItems", on_delete=models.PROTECT, verbose_name="Additional Item")
    total = models.DecimalField(verbose_name="Total", default=0, max_digits=30, decimal_places=2,)


class PagoPayPhone(ModeloBase):
    # GenericForeignKey
    content_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.PROTECT, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    modelo = GenericForeignKey('content_type', 'object_id')
    # ----------------------------------------------------------------
    email = models.CharField("Email", max_length=255, null=True, blank=True)
    cardType = models.CharField("cardType", max_length=255, null=True, blank=True)
    bin = models.TextField("bin", null=True, blank=True)
    lastDigits = models.CharField("lastDigits", max_length=20, null=True, blank=True)
    deferredCode = models.TextField("deferredCode", null=True, blank=True)
    deferred = models.BooleanField("deferred", null=True, blank=True)
    cardBrand = models.CharField("cardBrand", max_length=255, null=True, blank=True)
    amount = models.DecimalField("amount", max_digits=19, decimal_places=2)
    clientTransactionId = models.TextField("clientTransactionId", null=True, blank=True)
    phoneNumber = models.CharField("phoneNumber", max_length=255, null=True, blank=True)
    statusCode = models.CharField("statusCode", max_length=255, null=True, blank=True)
    transactionStatus = models.CharField("transactionStatus", max_length=255, null=True, blank=True)
    authorizationCode = models.CharField("authorizationCode", max_length=255, null=True, blank=True)
    messageCode = models.CharField("messageCode", max_length=255, null=True, blank=True)
    transactionId = models.CharField("transactionId", max_length=255, null=True, blank=True)
    document = models.CharField("document", max_length=100, null=True, blank=True)
    currency = models.CharField("currency", max_length=20, null=True, blank=True)
    optionalParameter2 = models.CharField("optionalParameter2", max_length=255, null=True, blank=True)
    storeName = models.CharField("storeName", max_length=255, null=True, blank=True)
    date = models.DateTimeField("date", null=True, blank=True)
    regionIso = models.CharField("regionIso", max_length=50, null=True, blank=True)
    transactionType = models.CharField("transactionType", max_length=255, null=True, blank=True)
    datajson = models.TextField("Respuesta Api")
    camposdiferentes = models.BooleanField("El api devolvió diferentes campos")

    def __str__(self):
        return self.datajson

    @staticmethod
    def registrar(modelo, data):
        import json
        from core.funciones import round_num_dec
        from datetime import datetime

        obj = None

        try:
            camposA = ['email', 'cardType', 'bin', 'lastDigits', 'deferredCode', 'deferred', 'cardBrand', 'amount',
                       'clientTransactionId', 'phoneNumber', 'statusCode', 'transactionStatus', 'authorizationCode',
                       'messageCode',
                       'transactionId', 'document', 'currency', 'optionalParameter2', 'storeName', 'date', 'regionIso',
                       'transactionType']

            camposB = list(data.keys())

            camposA.sort()
            camposB.sort()

            data['datajson'] = json.dumps(data)
            data['modelo'] = modelo
            data['amount'] = round_num_dec(Decimal(str(int(data['amount']) / 100)))
            data['date'] = datetime.strptime(data['date'], "%Y-%m-%dT%H:%M:%S.%f") if 'date' in data else datetime.now()
            data['camposdiferentes'] = not (camposA == camposB)

            camposA = camposA + ['camposdiferentes', 'modelo', 'datajson']

            obj = PagoPayPhone.objects.create(
                **{x: data.get(x) for x in camposA}
            )
        except Exception as ex:
            print(ex)

        return obj


class PagoTransferencia(ModeloBase):
    # GenericForeignKey
    content_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.PROTECT, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    modelo = GenericForeignKey('content_type', 'object_id')
    # ----------------------------------------------------------------
    infobanco = models.CharField("Información Bancaria", max_length=1000)
    infopersona = models.CharField("Información del Dueño de la cueta", max_length=1000)

    def __str__(self):
        return "{}, {}".format(self.infobanco, self.infopersona)


class PagoPayPal(ModeloBase):
    # GenericForeignKey
    content_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.PROTECT, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    modelo = GenericForeignKey('content_type', 'object_id')
    # ----------------------------------------------------------------
    transactionId = models.CharField("transactionId", max_length=255, null=True, blank=True)
    transaction_status = models.CharField("Transaction Status", max_length=255, null=True, blank=True)
    currency_code = models.CharField("currency_code", max_length=20, null=True, blank=True)
    subtotal = models.DecimalField("subtotal", max_digits=19, decimal_places=2)
    shipping = models.DecimalField("shipping", max_digits=19, decimal_places=2)
    total = models.DecimalField("total", max_digits=19, decimal_places=2)
    paypal_fee = models.DecimalField("paypal_fee", max_digits=19, decimal_places=2, default=0)
    tiendaemail = models.CharField("tiendaemail", max_length=255, null=True, blank=True)
    tiendaid = models.CharField("tiendaid", max_length=255, null=True, blank=True)
    soft_descriptor = models.CharField("soft_descriptor", max_length=255, null=True, blank=True)
    clientenombres = models.CharField("clientenombres", max_length=255, null=True, blank=True)
    clienteemail = models.CharField("clienteemail", max_length=255, null=True, blank=True)
    clienteid = models.CharField("clienteid", max_length=255, null=True, blank=True)
    clientecountry_code = models.CharField("clientecountry_code", max_length=255, null=True, blank=True)
    final_capture = models.BooleanField("final_capture", null=True, blank=True)
    capture_id = models.TextField(null=True, blank=True, verbose_name="Capture ID")
    order_id = models.CharField("order_id", max_length=255, null=True, blank=True)
    authorization_id = models.CharField("authorization_id", max_length=255, null=True, blank=True)
    datajson = models.TextField("Respuesta Api")

    def __str__(self):
        return self.datajson

    @staticmethod
    def registrar(modelo, data, order_id, auth_id, capture_id):
        import json
        from core.funciones import round_num_dec

        obj = None

        try:
            auth = data['purchase_units'][0]['payments']['authorizations'][0] if 'purchase_units' in data and\
                                                                                 len(data['purchase_units']) > 0 and \
                                                                                 'payments' in data['purchase_units'][0] and \
                                                                                 'authorizations' in data['purchase_units'][0]['payments'] and\
                                                                                len(data['purchase_units'][0]['payments']['authorizations']) > 0\
                                                                                else {'id': "No especificado"}
            amount = data['purchase_units'][0]['amount']
            obj = PagoPayPal.objects.create(
                modelo=modelo,
                transactionId=auth['id'],
                transaction_status=auth['status'],
                currency_code=amount['currency_code'],
                subtotal=round_num_dec(Decimal(str(amount['breakdown']['item_total']['value']))),
                shipping=round_num_dec(Decimal(str(amount['breakdown']['shipping']['value']))),
                total=round_num_dec(Decimal(str(amount['value']))),
                # paypal_fee=round_num_dec(Decimal(
                #     str(data['purchase_units'][0]['payments']['captures'][0]['seller_receivable_breakdown'][
                #             'paypal_fee']['value']))),
                tiendaemail=data['purchase_units'][0]['payee']['email_address'],
                tiendaid=data['purchase_units'][0]['payee']['merchant_id'],
                soft_descriptor=data['purchase_units'][0].get('soft_descriptor'),
                clientenombres="{} {}".format(data['payer']['name']['given_name'], data['payer']['name']['surname']),
                clienteemail=data['payer']['email_address'],
                clienteid=data['payer']['payer_id'],
                clientecountry_code=data['payer']['address']['country_code'],
                # final_capture=data['purchase_units'][0]['payments']['captures'][0]['final_capture'],
                order_id=order_id,
                authorization_id=auth_id,
                datajson=json.dumps(data),
                capture_id=capture_id
            )
        except Exception as ex:
            print(ex)

        return obj


class HistorialPedido(ModeloBase):
    pedido = models.ForeignKey(Pedido, verbose_name="Pedido", on_delete=models.PROTECT)
    user = models.ForeignKey(AUTH_USER_MODEL, verbose_name="Usuario que realizó la acción", on_delete=models.PROTECT, related_name='+')
    detalle = models.TextField("Observación")
    archivo = models.FileField(upload_to=UserUploadToPath("historialpedidos/archivos/"),
                               validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'tiff', "jfif", "pdf"]),
                                           validate_file_size_20mb], null=True, blank=True)
    estado = models.CharField("Acción", choices=ESTADO_PEDIDO, max_length=100)

    def typefile(self):
        if self.archivo:
            return self.archivo.name[self.archivo.name.rfind("."):]

    def __str__(self):
        return "{} - {}".format(self.get_estado_display(), self.user.username)

    def estado_pedido(self):
        return _estado_pedido(self)

    def es_estudiante(self):
        return self.pedido.user.id == self.user.id

    class Meta:
        ordering = ('-pk',)
        verbose_name = 'Historial de pedido'
        verbose_name_plural = 'Historial de pedidos'
        constraints = [
            models.CheckConstraint(check=Q(
                estado__in=list(x[0] for x in ESTADO_PEDIDO)),
                name='historialpedido__estado__in__ESTADO_PEDIDO'),
        ]
