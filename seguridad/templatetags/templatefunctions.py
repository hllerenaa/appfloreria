import json

from django.core import signing
from django import template
from django.template.defaultfilters import stringfilter

from autenticacion.models import Usuario
from seguridad.models import ModuloGrupo, Modulo, GroupModulo


register = template.Library()

def callmethod(obj, methodname):
    method = getattr(obj, methodname)
    if "__callArg" in obj.__dict__:
        ret = method(*obj.__callArg)
        del obj.__callArg
        return ret
    return method()


def args(obj, arg):
    if "__callArg" not in obj.__dict__:
        obj.__callArg = []
    obj.__callArg.append(arg)
    return obj


register.filter("call", callmethod)
register.filter("args", args)


def encrypt(value):
    myencrip = ""
    if type(value) is int:
        value = str(value)
    i = 1
    for c in value.zfill(20):
        myencrip = myencrip + chr(int(44450 / 350) - ord(c) + int(i / int(9800 / 4900)))
        i = i + 1
    return myencrip


@register.filter(is_safe=True)
@stringfilter
def truncatechars_middle(value, arg):
    try:
        ln = int(arg)
    except ValueError:
        return value
    if len(value) <= ln:
        return value
    else:
        return '{}...{}'.format(value[:ln//2], value[-((ln+1)//2):])


@register.filter
def get_encrypt(values):
    try:
        return signing.dumps(values, compress=True)
    except Exception as ex:
        return ""


@register.filter
def get_url_vars(path, dict_url_vars=""):
    try:
        dict_url_vars_completo = dict_url_vars or ""
        dict_url_vars_completo = json.loads(get_decrypt(dict_url_vars_completo.replace("dict_url_vars=", "")))
        dict_url_vars_completo = dict_url_vars_completo.get(path) or ""
        return "{}?{}".format(path, dict_url_vars_completo)
    except Exception as ex:
        return path

@register.filter
def split(val, sep=","):
    return val.split(sep)

@register.filter
def ordernarLista(lista):
    return sorted(lista)


@register.filter
def get_tipo_percent(self, name):
    return getattr(self, 'tipo_' + name)


@register.filter
def get_decrypt(cyphertxt):
    try:
        return signing.loads(cyphertxt)
    except Exception as ex:
        return ""


@register.filter
def convert_float_to_js(value):
    return str(value).replace(',', '.')


@register.filter
def get_color_tipo(val):
    COLOR_TIPO = (
        (1, "#767777"),
        (2, "#29B6F6"),
        (3, "#F39C12"),
        (4, "#138D75"),
    )
    return dict(COLOR_TIPO)[int(val)]


@register.simple_tag
def ver_valor_dict(dicionario, llave):
    return dicionario.get(llave)


@register.simple_tag
def ver_valor_dict_str(dicionario, llave, default):
    return str(dicionario.get(llave) or default)


@register.filter
def get_modulos(request):
    data = {}
    user = Usuario.objects.get(username=request.user.username)
    data['grupos'] = ModuloGrupo.objects.filter(status=True, modulos__id__in=list(
        GroupModulo.objects.filter(status=True, group__in=user.groups.all()).values_list('modulos__id'))).order_by(
        'prioridad')
    modulos = Modulo.objects.filter(url=request.path)
    if modulos.exists():
        if data['grupos'].filter(modulos__in=modulos, status=True).exists():
            data["group"] = data['grupos'].filter(modulos__in=modulos, status=True).first().nombre
    return data


@register.filter('startswith')
def startswith(text, starts):
    if isinstance(text, str):
        return text.lower().startswith(starts.lower())
    return False


@register.simple_tag
def traducir_permiso(value):
    valor = str(value).lower()
    es_permiso_de_django = 'can add' in valor or 'can view' in valor or 'can change' in valor or 'can delete' in valor
    if es_permiso_de_django:
        return ' '.join(valor.replace("can", "Puede") \
                        .replace('add', 'Agregar') \
                        .replace('view', 'Ver') \
                        .replace('delete', 'Eliminar') \
                        .replace('change', 'Modificar').split(' ')[0:2])
    return value


def calendarbox(var, dia):
    return var[dia]

def filter_fecha_turno(qs, dia):
    dias = {
        7: 1,
        6: 7,
        5: 6,
        4: 5,
        3: 4,
        2: 3,
        1: 2
    }
    return qs.filter(fecha_turno__week_day=dias[dia])

def calendarboxdetails(var, dia):
    lista = var[dia]
    result = []
    for x in lista:
        b = [x.split(',')[0], x.split(',')[1]]
        result.append(b)
    return result

register.filter("calendarbox", calendarbox)
register.filter("calendarboxdetails", calendarboxdetails)
register.filter("filter_fecha_turno", filter_fecha_turno)