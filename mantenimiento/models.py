from django.db import models
import re
from core.funciones_adicionales import round_num_dec
from core.validadores import solo_numeros
from django.db.models import Sum, Avg, Q
from django.db.models.functions import Coalesce
from django.db.models import Q
from core.constantes import SIMBOLO_MONEDA
from core.custom_models import ModeloBase
from django.utils.text import slugify
from decimal import Decimal
from django.core.validators import MinValueValidator, FileExtensionValidator, MaxValueValidator


class RedesSociales(ModeloBase):
    nombre = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Nombre')
    icono = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Ícono')
    href = models.URLField(max_length=1000, blank=True, null=True, verbose_name='Url')
    status = models.BooleanField(default=True)

    def __str__(self):
        return "{} - {} [{}]".format(self.icono, self.href, self.status)

    class Meta:
        verbose_name = 'Rede Social'
        verbose_name_plural = 'Redes Sociales'


class Carousel(ModeloBase):
    orden = models.IntegerField(verbose_name='Orden')
    imagen = models.FileField(upload_to='carousel/1/', max_length=600, blank=True, null=True, verbose_name='Imágen 2000x500px')
    titulo_1 = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Título 1')
    # titulo_2 = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Título 2')
    detalle = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Detalle')
    url_boton = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Url Boton')
    texto_boton = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Texto Boton')
    publicado = models.BooleanField(default=False, verbose_name='Publicado')

    def publicado_activo(self):
        if self.publicado:
            return "fas fa-check-circle text-success"
        else:
            return "fas fa-times-circle text-danger"

    def __str__(self):
        return "Orden: {} - {} [{}]".format(self.orden, self.titulo_1, self.status)

    class Meta:
        verbose_name = 'Carrousel'
        verbose_name_plural = 'Carrouseles'
        ordering = ('orden', 'status')


class Producto(ModeloBase):
    orden = models.IntegerField(default=0, verbose_name='Orden de Visualización')
    nombre = models.CharField(max_length=1000, blank=True, null=True, verbose_name="Nombre")
    precio = models.DecimalField(default=0, max_digits=19, decimal_places=2, verbose_name="Pvp", validators=[MinValueValidator(Decimal('0'))])
    slug = models.SlugField(null=True, blank=True, editable=False)
    descripcion = models.TextField(null=True, blank=True, verbose_name="Descripción")
    foto1 = models.ImageField(upload_to="fotoproductos/1/", blank=True, null=True, verbose_name='Foto 1 900x1200px')
    foto2 = models.ImageField(upload_to="fotoproductos/2/", blank=True, null=True, verbose_name='Foto 2 900x1200px')
    foto3 = models.ImageField(upload_to="fotoproductos/3/", blank=True, null=True, verbose_name='Foto 3 900x1200px')
    foto4 = models.ImageField(upload_to="fotoproductos/4/", blank=True, null=True, verbose_name='Foto 4 900x1200px')
    activo = models.BooleanField(default=True, verbose_name='¿Visible?')

    def numitems(self):
        return self.productoitems_set.values('id').filter(status=True).count()

    def listitems(self):
        return self.productoitems_set.filter(status=True, visible=True).order_by('orden')

    def __str__(self):
        return '{}'.format(self.nombre)

    def get_foto1(self):
        imagen = ''
        if self.foto1:
            imagen = self.foto1.url
        return imagen

    def get_foto2(self):
        imagen = ''
        if self.foto2:
            imagen = self.foto2.url
        return imagen

    def save(self, *args, **kwargs):
        super(Producto, self).save(*args, **kwargs)
        self.slug = slugify(self.nombre)
        if Producto.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug += str(self.pk)
        super(Producto, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'


class ProductoItems(ModeloBase):
    orden = models.IntegerField(default=1, verbose_name='Orden')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Producto')
    nombre = models.CharField(max_length=1000, null=True, blank=True, verbose_name='Nombres')
    precio = models.DecimalField(default=0, max_digits=19, decimal_places=2, verbose_name="Pvp", validators=[MinValueValidator(Decimal('0'))])
    foto1 = models.ImageField(upload_to="adicionalesitems/1/", blank=True, null=True, verbose_name='Foto 1 900x1200px')
    visible = models.BooleanField(default=True, verbose_name='Visible')

    def get_foto1(self):
        imagen = ''
        if self.foto1:
            imagen = self.foto1.url
        return imagen

    def str_visible(self):
        return 'fa fa-check-circle text-success' if self.visible else 'fa fa-times-circle text-danger'

    def __str__(self):
        return "{}, {} ({})".format(self.producto, self.nombre, self.orden)

    def save(self, *args, **kwargs):
        super(ProductoItems, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Producto Items Adicional'
        verbose_name_plural = 'Producto Items Adicionales'


class Couriers(ModeloBase):
    agencia = models.CharField(max_length=250, verbose_name='Agencia')
    nombre = models.CharField(max_length=250, verbose_name='Nombre')
    telefono = models.CharField(max_length=100, verbose_name='Teléfono', validators=[solo_numeros])
    email = models.EmailField(blank=True, null=True, verbose_name='Correo Electrónico')

    def __str__(self):
        return "{}, {}".format(self.agencia, self.nombre)

    class Meta:
        verbose_name = 'Couriers'
        verbose_name_plural = 'Couriers'
        ordering = ('nombre',)