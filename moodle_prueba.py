import os, sys
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appfloreria.settings')

application = get_wsgi_application()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from area_geografica.models import Pais, Provincia, Ciudad, Parroquia
from appfloreria.settings import BASE_DIR
from django.db import transaction, connection
import openpyxl
import json
from seguridad.models import *
from django.db import transaction, connections
from datetime import date, datetime, timedelta
import time
from hashlib import md5

start = datetime.strptime(f"{datetime.now().date()} {datetime.now().hour}:{datetime.now().minute}", '%Y-%m-%d %H:%M')
fcreacion = int(time.mktime(start.timetuple()))

#necesario pip install passlib

def crearUsuario(numprueba, tp=1):
    try:
        username = f'userprueba{numprueba}'
        first_name = 'User'
        last_name = f'Prueba {numprueba}'
        email = f'{username}@unemi.edu.ec'
        idnumber = f'09285415561'

        with connections['moodle_db'].cursor() as cursor:
            sql1_ = f"SELECT 'x' FROM mooc_user WHERE username = '{username}' AND mnethostid = '1' LIMIT 1"
            sql2_ = f"SELECT 'x' FROM mooc_user WHERE LOWER(email) = LOWER('{email}') AND mnethostid = '1' LIMIT 1;"
            cursor.execute(sql1_)
            consultausername_ = cursor.fetchall()
            cursor.execute(sql2_)
            consultaemail_ = cursor.fetchall()
            print(consultaemail_, consultausername_)
            if not consultausername_:
                if not consultaemail_:
                    print(f'Creando usuario...')
                    if tp == 1:
                        auth_ = 'manual'
                        # pass_ = pbkdf2_sha256.hash(idnumber, salt=str('moodlesalt').encode('utf-8'), rounds=10000)
                        pass_ = md5(idnumber.encode("utf-8")).hexdigest()
                        print(pass_)
                    else:
                        auth_ = 'db'
                        pass_ = 'not cached'
                    sql3_ = f"INSERT INTO mooc_user (username, auth, PASSWORD, firstname, lastname, email, city, country, idnumber, lang, calendartype, confirmed, mnethostid, maildisplay, mailformat, maildigest, autosubscribe, trackforums, timecreated, timemodified)" \
                            f" VALUES('{username}', '{auth_}', '{pass_}',  '{first_name}', '{last_name}', '{email}', '', '', '{idnumber}', 'es', 'gregorian', '1', '1', '2', '1', '0', '1', '0', '{fcreacion}', '{fcreacion}');"
                    cursor.execute(sql3_)
                    sql4_ = f"SELECT id FROM mooc_user WHERE username = '{username}' AND mnethostid = '1' LIMIT 1"
                    cursor.execute(sql4_)
                    result4_ = cursor.fetchall()
                    if result4_:
                        idusuario = result4_[0][0]
                        print(f'Usuario creado id: {idusuario}')
                        print(f'Creando contexto...')
                        sql5_ = f"INSERT INTO mooc_context (contextlevel, instanceid, DEPTH, PATH, locked) VALUES('30', '{idusuario}', '0', NULL, '0') RETURNING id;"
                        cursor.execute(sql5_)
                        sql6_ = f"SELECT * FROM mooc_context WHERE contextlevel = '30' AND instanceid = '{idusuario}';"
                        cursor.execute(sql6_)
                        result6_ = cursor.fetchall()
                        if result6_:
                            idcontext = result6_[0][0]
                            print(f'Contexto creado id: {idcontext}')
                            sql7 = f"UPDATE mooc_context SET contextlevel = '30',instanceid ='{idusuario}', depth = '2',path = '/1/{idcontext}', locked = '0' WHERE id='{idcontext}';"
                            cursor.execute(sql7)
                    cursor.close()
                    return idusuario
                else:
                    print(f"El correo {email} ya esta en uso")
                    return False
            else:
                print(f"El username {username} ya esta en uso")
                return False
    except Exception as ex:
        print(f'{ex} - Error on line {sys.exc_info()[-1].tb_lineno}')
        return False


def crearCurso(idusuario, cursonombre, rolestudiante):
    try:
        with connections['moodle_db'].cursor() as cursor:
            sql1_ = f"SELECT id FROM mooc_course WHERE idnumber = '{cursonombre}' ORDER BY id ASC"
            cursor.execute(sql1_)
            result1_ = cursor.fetchall()
            if result1_:
                idcurso = result1_[0][0]
                sql2_ = f"SELECT id FROM mooc_context WHERE contextlevel = '50' AND instanceid = '{idcurso}'"
                cursor.execute(sql2_)
                result2_ = cursor.fetchall()
                if result2_:
                    idcontext = result2_[0][0]
                    sql3_ = f"SELECT id FROM mooc_enrol WHERE courseid = '15' AND status = '0'  ORDER BY sortorder,id;"
                    cursor.execute(sql3_)
                    result3_ = cursor.fetchall()
                    if result3_:
                        idrolmanual = result3_[0][0]
                        sql4_ = f"SELECT * FROM mooc_user_enrolments WHERE enrolid = '{idrolmanual}' AND userid ='{idusuario}'"
                        cursor.execute(sql4_)
                        result4_ = cursor.fetchall()
                        if not result4_:
                            print(f"Inscribiendo...")
                            sql5_ = f"INSERT INTO mooc_user_enrolments (enrolid, status, userid, timestart, timeend, modifierid, timecreated, timemodified)" \
                                    f"VALUES('{idrolmanual}', '0', '{idusuario}', '0', '0', '2', '{fcreacion}', '{fcreacion}')"
                            cursor.execute(sql5_)
                            sql6_ = f"SELECT * FROM mooc_role_assignments WHERE roleid = '{rolestudiante}' AND contextid = '{idcontext}' AND userid = '{idusuario}' AND component = '' AND itemid = '0'  ORDER BY id"
                            cursor.execute(sql6_)
                            result6_ = cursor.fetchall()
                            if not result6_:
                                print(f"Confirmar inscripción...")
                                sql7_ = f"INSERT INTO mooc_role_assignments (roleid, contextid, userid, component, itemid, timemodified, modifierid, sortorder) " \
                                        f"VALUES('{rolestudiante}', '{idcontext}', '{idusuario}', '', '0', '{fcreacion}', '2', '0')"
                                cursor.execute(sql7_)
                                sql8_ = f"SELECT * FROM mooc_cache_flags WHERE name = '{idusuario}' AND flagtype = 'accesslib/dirtyusers' LIMIT 1"
                                cursor.execute(sql8_)
                                result8_ = cursor.fetchall()
                                if not result8_:
                                    print(f"Creando Cache...")
                                    sql9_ = f"INSERT INTO mooc_cache_flags (flagtype, name, value, expiry, timemodified) " \
                                            f"VALUES('accesslib/dirtyusers', '{idusuario}', '1', '{fcreacion}','{fcreacion}')"
                                    cursor.execute(sql9_)
                                cursor.close()
                            else:
                                print(f'Usuario ya esta en role_assignments')
                                return False
                        else:
                            print(f'Usuario ya esta enrolado')
                            return False
                else:
                    print(f'Curso no tiene contexto')
                    return False
    except Exception as ex:
        print(f'{ex} - Error on line {sys.exc_info()[-1].tb_lineno}')
        return False

# for i in range(1010, 1500):
#     idusuario_ = crearUsuario(i)
#     if idusuario_:
#         crearCurso(idusuario_, 'PERIODO1-2023-CUR6-INS11', 5)
# try:
#     with connections['moodle_db'].cursor() as cursor:
#         sql1_ = f"SELECT id FROM mooc_user ORDER BY id ASC"
#         cursor.execute(sql1_)
#         result1_ = cursor.fetchall()
#         if result1_:
#             for rid in result1_:
#                 crearCurso(rid[0], 'PERIODO1-2023-CUR6-INS11', 5)
#                 print(f"------------------------------------------")
# except Exception as ex:
#     transaction.set_rollback(True)
#     print(f'{ex} - Error on line {sys.exc_info()[-1].tb_lineno}')


crearUsuario(1756)
# crearCurso(1072, 'PERIODO1-2023-CUR6-INS11', 5)