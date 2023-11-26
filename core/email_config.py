import threading
from django.core.mail import get_connection
from django.core.mail.message import EmailMessage
from django.template.loader import get_template
from appfloreria.settings import EMAIL_USE_TLS, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD


def conectar_cuenta():
    conectar = get_connection()
    return conectar


class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list, recipient_list_cc, adjuntos, coneccion):
        self.subject = subject
        self.recipient_list = recipient_list
        self.recipient_list_cc = recipient_list_cc
        self.html_content = html_content
        self.adjuntos = adjuntos
        self.coneccion = coneccion

        threading.Thread.__init__(self)

    def run(self):
        if self.coneccion:
            msg = EmailMessage(self.subject, self.html_content, self.coneccion.username, self.recipient_list,
                               bcc=self.recipient_list_cc, connection=self.coneccion)
        else:
            msg = EmailMessage(self.subject, self.html_content, EMAIL_HOST_USER, self.recipient_list,
                               bcc=self.recipient_list_cc)
        msg.content_subtype = "html"
        if self.adjuntos:
            for adjunto in self.adjuntos:
                msg.attach(
                    adjunto['filename'],
                    adjunto['content'],
                    adjunto.get("mimetype")
                )
        msg.send()


def send_html_mail(subject, html_template, datos, recipient_list, recipient_list_cc, adjuntos=None):
    try:
        if recipient_list.__len__() or recipient_list_cc.__len__():
            template = get_template(html_template)
            d = datos
            html_content = template.render(d)
            EmailThread(subject, html_content, recipient_list, recipient_list_cc, adjuntos, conectar_cuenta()).start()
    except Exception as ex:
        pass