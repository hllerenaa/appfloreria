# # coding=utf-8
# import os
# import io as StringIO
# import sys
#
# from appfloreria import settings
# from appfloreria.settings import MEDIA_ROOT, MEDIA_URL, BASE_DIR, STATIC_URL, STATIC_ROOT, SITE_STORAGE, DEBUG
# from django.template.loader import get_template
# from xhtml2pdf import pisa
# from django.http import HttpResponse, JsonResponse
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont, TTFOpenFile
# from reportlab.graphics.shapes import Drawing
# from xhtml2pdf.default import DEFAULT_FONT, DEFAULT_CSS
#
#
# def link_callback(uri, rel):
#     sUrl = settings.STATIC_URL       # Typically /static/
#     sRoot = os.path.join(BASE_DIR, 'static')    # Typically /home/userX/project_static/
#     mUrl = settings.MEDIA_URL       # Typically /static/media/
#     mRoot = os.path.join(BASE_DIR, 'media')    # Typically /home/userX/project_static/media/
#
#     if uri.startswith(mUrl):
#         path = os.path.join(mRoot, uri.replace(mUrl, ""))
#     elif uri.startswith(sUrl):
#         path = os.path.join(sRoot, uri.replace(sUrl, ""))
#     else:
#         return uri                  # handle absolute uri (ie: http://some.tld/foo.png)
#     print(path)
#     # make sure that file exists
#     if not os.path.isfile(path):
#         raise Exception('media URI must start with %s or %s' % (sUrl, mUrl))
#
#
# def conviert_html_to_pdf(template_src, context_dict):
#     try:
#         template = get_template(template_src)
#         html = template.render(context_dict).encode(encoding="UTF-8")
#         result = StringIO.BytesIO()
#         pisaStatus = pisa.CreatePDF(StringIO.BytesIO(html), result, link_callback=link_callback)
#         if not pisaStatus.err:
#             return HttpResponse(result.getvalue(), content_type='application/pdf')
#         return JsonResponse({"result": "bad", "mensaje": u"Problemas al ejecutar el reporte."})
#     except Exception as ex:
#         return JsonResponse({"result": False, "mensaje": f"Problemas al ejecutar el reporte. {ex} {'Error on line {}'.format(sys.exc_info()[-1].tb_lineno)}"})
#
#
# def view_certificados(template_src, context_dict):
#     try:
#         URL_MEDIA, URL_STATIC = os.path.join(BASE_DIR, 'media'), os.path.join(BASE_DIR, 'static')
#         template = get_template(template_src)
#         html = template.render(context_dict).encode(encoding="UTF-8")
#         result = StringIO.BytesIO()
#         pdfmetrics.registerFont(TTFont('zhfont', os.path.join(URL_STATIC, 'fonts/Great_Vibes/GreatVibes-Regular.ttf')))
#         DEFAULT_FONT["helvetica"] = "zhfont"
#         pisaStatus = pisa.CreatePDF(StringIO.BytesIO(html), result, link_callback=link_callback)
#         if not pisaStatus.err:
#             return HttpResponse(result.getvalue(), content_type='application/pdf')
#         return JsonResponse({"result": False, "mensaje": u"Problemas al ejecutar el reporte."})
#     except Exception as ex:
#         return JsonResponse({"result": False, "mensaje": f"Problemas al ejecutar el reporte. {ex} {'Error on line {}'.format(sys.exc_info()[-1].tb_lineno)}"})
#
#
# def save_certificados(template_src, context_dict, filename, output_folder):
#     URL_MEDIA, URL_STATIC = os.path.join(BASE_DIR, 'media'), os.path.join(BASE_DIR, 'static')
#     template = get_template(template_src)
#     html = template.render(context_dict).encode(encoding="UTF-8")
#     os.makedirs(output_folder, exist_ok=True)
#     filepdf = open(output_folder + os.sep + filename, "w+b")
#     pdfmetrics.registerFont(TTFont('zhfont', os.path.join(URL_STATIC, 'fonts/Great_Vibes/GreatVibes-Regular.ttf')))
#     DEFAULT_FONT["helvetica"] = "zhfont"
#     pdf1 = pisa.pisaDocument(StringIO.BytesIO(html), dest=filepdf, link_callback=link_callback)
#     if not pdf1.err:
#         return True
#     return JsonResponse({"result": False, "mensaje": u"Problemas al ejecutar el reporte."})
#
#
