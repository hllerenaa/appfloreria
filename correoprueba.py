import os, sys

from django.core.wsgi import get_wsgi_application
# import telebot
from datetime import datetime, date, time, timedelta
import requests


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appfloreria.settings')
application = get_wsgi_application()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from django.db import transaction
from django.contrib.auth.models import User
from seguridad.models import Configuracion
from core.email_config import send_html_mail


try:
    subject = "⏰ El ISTER te recuerda"
    to = ['hllerenaa1h@gmail.com',]
    template_email = 'email/email_notificacion.html'
    send_html_mail(subject, template_email, {}, to, [], None)
except Exception as ex:
    linea_ = 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno)
    print(ex, linea_)


