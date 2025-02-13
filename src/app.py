"""**Writing docstrings**

There are several different docstring formats which one can use in order to enable Sphinx's
autodoc extension to automatically generate documentation. For this tutorial we will use
the Sphinx format, since, as the name suggests, it is the standard format used with Sphinx.
Other formats include Google (see here) and NumPy (see here), but they require the use of 
Sphinx's napoleon extension, which is beyond the scope of this tutorial."""


from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required
#from config import config
import time
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import json
# pandas:
import pandas as pd



import gspread
# ============================================================================
# Models:
# ============================================================================
# SQL QUERY MODELS
from src.models.ModelUser import ModelUser
from src.models.ModelUser import ModelAdmin
# Entities:
from src.models.entities.User import User
# MODEL REPORTES
from src.reportes.backend.dll_copy import ExcelServicios
from src.reportes.backend.dll_copy import ExcelAdmin2
from src.reportes.backend.dll_copy import ExcelSia
from src.reportes.backend.dll_copy import ExcelFacultades
# FUNCIONES AUXILIARE
from src.reportes.backend.dll_copy import allowed_file
from src.reportes.backend.dll_copy import files_in_data
from src.reportes.backend.dll_copy import  render_informe
#from src.reportes.backend.dll_copy import  unir_regiones
#from src.reportes.backend.dll_copy import  read_json_file


# Nuevo requerimiento psl
from src.reportes.backend.dll_copy import asistenciaOriginal_to_estandar_AV
from src.reportes.backend.dll_copy import asistenciaOriginal_to_estandar_TIC


# Nuevo
import ast
import traceback


# Nuevo requerimiento STEM
from src.reportes.backend.dll_copy import main_capacitaciones
from src.reportes.backend.dll_copy import main_manuales
from src.reportes.backend.dll_copy import main_ETL
from src.reportes.backend.dll_copy import concatenar_stem


# Autoevaluación:
from src.reportes.backend.dll_copy import main_autoeval


# SEDE:
from src.reportes.backend.dll_copy import inicializador_cols, load_data_sede, preprocessing_sede
from src.reportes.backend.dll_copy import  main_matriculados, main_bloq_admin, main_bloq_academ
from src.reportes.backend.dll_copy import  check_repeat_main


# Contantes

from src.reportes.backend.config_constants import my_config_constants
from src.reportes.backend.dll_copy import format_column

# ============================================================================
# OBJETOS:
# ============================================================================
app = Flask(__name__)

# ============================================================================
# CONFIGURACION DATABASE and folder file:
# ============================================================================
app.config['SECRET_KEY'] = my_config_constants["flask_secret_key"]
app.config['MYSQL_HOST'] = my_config_constants["mysql_host"]
app.config['MYSQL_USER'] = my_config_constants["mysql_username"]
app.config['MYSQL_PASSWORD'] = my_config_constants["mysql_password"]
app.config['MYSQL_DB'] = my_config_constants["mysql_db"]
app.config['UPLOAD_FOLDER'] = my_config_constants["upload_folder"]

# COMTIMUACION

CSRFProtect(app)
db = MySQL(app)
login_manager_app = LoginManager(app)
# MODELOS:
PATH_PRINCIPAL = my_config_constants["principal_path"]
# MODEL NUEVOS:
MODEL_SERVICIOS = ExcelServicios(PATH_PRINCIPAL)
MODEL_ADMIN = ExcelAdmin2(PATH_PRINCIPAL)
MODEL_SIA = ExcelSia(PATH_PRINCIPAL)
MODEL_FACULTADES = ExcelFacultades(PATH_PRINCIPAL)





# ============================================================================
# Login:
# ============================================================================
# Login por el ID en base de datos:
@login_manager_app.user_loader
def load_user(id):
    """Esta funcion identifica mediante el id en la base de datos si el usuario esta logueado.

    :param id: id del usuario, defaults to None
    :type id: int
    :return: usuario por id
    :rtype: None
    """
    return ModelUser.get_by_id(db, id)
# Ruta principal para hacer login:
@app.route('/')
def index():
    """Esta funcion re dirige a la pagina de login.

    :param None: No recibe funcion.
    :type: None
    :return: Redireccion a la pagina de loguin.
    :rtype: None
    """
    return redirect(url_for('login'))
# Control Login:
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Esta funcion permite renderizar el html de login, y busca al usuario en la base de datos, controla
    en caso de que no este registrado o que la contraseña sea incorrecta, en caso de que los datos esten correctos,
    este redirige hacia la pagina principal del usuario asignandole un rol que viene por defecto en la base de datos.

    :param None: No recibe funcion.
    :type: None
    :return: Redireccion a la pagina de loguin.
    :rtype: None
    """
    if request.method == 'POST':
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(db, user)
        if logged_user != None:
            if logged_user.password: # Booleano
                login_user(logged_user)
                # ROLES to HOME:
                # ============================================ 
                if logged_user.rol == '1':
                    # ADMIN
                    session['rol'] = logged_user.rol
                    session['id'] = logged_user.id
                    session['username'] = logged_user.username
                    return redirect(url_for('home_admin'))
                
                elif logged_user.rol == '2':
                    # SIA
                    session['rol'] = logged_user.rol
                    session['id'] = logged_user.id
                    session['username'] = logged_user.username
                    return redirect(url_for('home_sia'))
                
                elif logged_user.rol == '3':
                    # ACOMPAÑAMIENTO
                    session['rol'] = logged_user.rol
                    session['id'] = logged_user.id
                    session['username'] = logged_user.username
                    return redirect(url_for('home_acompanamiento'))

                elif logged_user.rol == '4':
                    # STEM
                    session['rol'] = logged_user.rol
                    session['id'] = logged_user.id
                    session['username'] = logged_user.username
                    return redirect(url_for('home_stem'))

                elif logged_user.rol == '5':
                    # PSL
                    session['rol'] = logged_user.rol
                    session['id'] = logged_user.id
                    session['username'] = logged_user.username
                    return redirect(url_for('home_psl'))
                
                elif logged_user.rol == '9':
                    # UNAL EN LA REGION
                    session['rol'] = logged_user.rol
                    session['id'] = logged_user.id
                    session['username'] = logged_user.username
                    return redirect(url_for('home_bot_IA'))
                elif logged_user.rol == '10':
                    # SEDE
                    session['rol'] = logged_user.rol
                    session['id'] = logged_user.id
                    session['username'] = logged_user.username
                    return redirect(url_for('home_sede'))
                elif logged_user.rol == '11':
                    # AUTOEVALUACION
                    session['rol'] = logged_user.rol
                    session['id'] = logged_user.id
                    session['username'] = logged_user.username
                    return redirect(url_for('home_autoeval'))
                else:
                    flash("No hay rol especifico")
                    return render_template('auth/login.html')
                # ============================================ 
            else:
                flash("Invalid password...")
                return render_template('auth/login.html')
        else:
            flash("User not found...")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')

# Cerrar Sesion:
@app.route('/logout')
def logout():
    """Esta funcion permite hacer el logout a cualquier usuario, despues redirije a la pagina principal de login.

    :param None: No recibe funcion.
    :type: None
    :return: Redireccion a la pagina de loguin.
    :rtype: None
    """
    logout_user()
    return redirect(url_for('login'))


# ============================================================================
# AYUDA:
# ============================================================================
@app.route('/home_ayuda')
@login_required
def home_ayuda():
    try:
        back = session['back_url']
        return render_template('home_ayuda.html', back=back)
    except:
        back = "#"
        return render_template('home_ayuda.html', back=back)


# ============================================================================
# ADMINISTRADOR:
# ============================================================================
# HOME:
@app.route('/home_admin')
@login_required
def home_admin():
    if session['rol'] == '1':
        session['back_url'] = url_for('home_admin')
        return render_template('home_admin.html')
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')
# API:
@app.route('/home_api', methods=['GET','POST'])
@login_required
def home_api():
    if session['rol'] == '1':
        if request.method == 'POST':
            mensaje = ModelAdmin.create(db,
                                        request.form['username'],
                                        request.form['password'],
                                        request.form['fullname'],
                                        request.form['rol'],
                                        request.form['date_mod'])
            flash(mensaje)
            return redirect(url_for('home_api'))
        else:
            return render_template('admin/home_api.html')
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# REPORTES ADMIN:
@app.route('/home_reportes_generales')
@login_required
def home_reportes_generales():
    if session['rol'] == '1':
        session['back_url'] = url_for('home_reportes_generales')
        session['path'] = os.path.join("admin","admin_reportes_generales")
        session['report'] = 1
        session['required_files'] = ['Matriculados_Informacion_Basica_ant.xlsx',
                                    'Matriculados_Informacion_Basica_presente.xlsx',
                                    'SPP.xlsx',
                                    'Matriculados_por_periodo.xlsx',
                                    'Inscripcion_de_asignaturas.xlsx']
        session['download_file'] =  ['siapss.xlsx']
        session['path_template'] =  'admin/home_general_files.html'
        session['file'] = 'siapss.xlsx'
        session['servicio'] = 'SIA + programa de Gov'
        id = session['id']
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        # Como admin no tiene coneccion don DB
        # se guarda la session['data'] vacia
        session['data']=None
        session['link']=None
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')


# ============================================================================
# SIA:
# ============================================================================
# HOME:
@app.route('/home_sia')
@login_required
def home_sia():
    if session['rol'] == '2':
        session['back_url'] = url_for('home_sia')
        return render_template('home_sia.html')
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# MI-MATRICULADOS:
@app.route('/matriculados')
@login_required
def home_matriculados():
    if session['rol'] == '2':
        session['back_url'] = url_for('home_matriculados')
        session['path'] = os.path.join("sia")
        session['report'] = 21
        session['required_files'] = ['Matriculados_Informacion_Basica_ant.xlsx', # semestre anterior
                                    'Matriculados_Informacion_Basica_presente.xlsx', # este semestre
                                    'Matriculados_por_periodo.xlsx',
                                    'Matriculados_Informacion_Basica.xlsx',
                                    'Inscripcion_de_asignaturas.xlsx']
        session['download_file'] =  ['matriculados.xlsx']
        session['path_template'] =  'sia/home_matriculados.html'
        session['file'] = 'matriculados.xlsx'
        session['servicio'] = 'SIA matriculados'
        id = session['id']
        
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        # Con nuevo template, se customisa desde acá.
        session['link'] = "https://datastudio.google.com/embed/reporting/58096be2-05ee-482d-bbe2-15998995d533/page/3aE0C"
        session['table'] = None
        session['data'] = []


        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')
    
# ESTADISTICAS:
@app.route('/estadisticas')
@login_required
def home_estadisticas():
    if session['rol'] == '2':
        session['back_url'] = url_for('home_estadisticas')
        session['path'] = os.path.join("sia")
        session['report'] = 22
        session['required_files'] = ['horarios_y_grupos.xlsx',
                                    'asignaturas_inscritas.xlsx']
        session['download_file'] =  ['estadisticas.xlsx']
        session['path_template'] =  'sia/home_estadisticas.html'
        session['file'] = 'estadisticas.xlsx'
        session['servicio'] = 'SIA estadisticas'
        id = session['id']
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        
        session['link'] = 'https://datastudio.google.com/embed/reporting/66e9b53f-c19c-44c8-b5f6-37fe26d3812d/page/ohz7C" frameborder="0" style="border:0'
        session['table'] = None
        session['data'] = []
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# PROYECTOS Y TESIS:
@app.route('/proyectos_tesis')
@login_required
def home_proyectos_y_tesis():
    if session['rol'] == '2':
        session['back_url'] = url_for('home_proyectos_y_tesis')
        session['path'] = os.path.join("sia")
        session['report'] = 23
        session['required_files'] = ['horarios_y_grupos.xlsx', # semestre anterior
                                    'asignaturas_inscritas.xlsx']
        session['download_file'] =  ['proyectos_y_tesis.xlsx']
        session['path_template'] =  'sia/home_tesis_proyectos_grado.html'
        session['file'] = 'proyectos_y_tesis.xlsx'
        session['servicio'] = 'SIA proyectos y tesis'
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        
         # Con nuevo template, se customisa desde acá.
        session['link'] = "https://datastudio.google.com/embed/reporting/4580b4bc-3bc3-4d8c-b12b-daa7eb06d720/page/Xc77C"
        session['table'] = None
        session['data'] = []
        
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')  

# TUTORES:
@app.route('/tutores')
@login_required
def home_tutores():
    if session['rol'] == '2':
        session['back_url'] = url_for('home_tutores')
        session['path'] = os.path.join("sia")
        session['report'] = 24
        session['required_files'] = ['tutores.xlsx','Matriculados_Informacion_Basica_presente_tutores.xlsx']
        session['download_file'] =  ['tutores.xlsx']
        session['path_template'] =  'sia/home_tutores.html'
        session['file'] = 'tutores.xlsx'
        session['servicio'] = 'SIA tutores'
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        
        # Con nuevo template, se customisa desde acá.
        session['link'] = "https://lookerstudio.google.com/embed/reporting/990b2893-601c-4da9-8536-8dba40da7add/page/UYfDD"
        session['table'] = None
        session['data'] = []
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# ============================================================================
# ACOMPAÑAMIENTO:
# ============================================================================
# HOME:
@app.route('/home_acompanamiento')
@login_required
def home_acompanamiento():
    if session['rol'] == '3':
        session['back_url'] = url_for('home_acompanamiento')
        return render_template('home_acompanamiento.html')
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# acompanamiento_unal_lee:
@app.route('/unal_lee')
@login_required
def home_unal_lee():
    if session['rol'] == '3':
        session['back_url'] = url_for('home_unal_lee')
        session['path'] = os.path.join("acompanamiento")
        session['report'] = 31
        session['required_files'] = ['unal_lee.xlsx']
        session['download_file'] =  ['unal_lee.xlsx']
        session['path_template'] =  'acompanamiento/home_acmp_user.html'
        session['servicio'] = 'unal_lee'
        session['file'] = 'unal_lee.xlsx'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/d21f07b1-c4a9-4b73-8502-211c48dea73e/page/p_xb12c0l57c'
        session['table'] = 'acmp_1' 
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        # Fecha:
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        # get user and date from db:
        df_dates = ModelUser.get_distinct_V2(db,  "acmp_1")
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# acompanamiento_tramites_solicitudes:
@app.route('/tramites_y_solcitudes')
@login_required
def home_tramites_y_solicitudes():
    if session['rol'] == '3':
        session['back_url'] = url_for('home_tramites_y_solicitudes')
        session['path'] = os.path.join("acompanamiento")
        session['report'] = 32
        session['required_files'] = ['tramites_solicitudes.xlsx']
        session['download_file'] =  ['tramites_solicitudes.xlsx']
        session['path_template'] =  'acompanamiento/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/b0fe10ca-69ae-48b5-b84f-ec10c81a0b6d/page/p_jwrt34r88c'
        session['table'] = 'acmp_2' 
        # Ayuda:
        session['servicio'] = 'tramites_y_solicitudes'
        session['file'] = 'tramites_solicitudes.xlsx'
        
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        # Fecha:
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        # get user and date from db:
        # get user and date from db:
        df_dates = ModelUser.get_distinct_V2(db,  "acmp_2")
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# acompanamiento_focad
@app.route('/focad')
@login_required
def home_focad():
    if session['rol'] == '3':
        session['back_url'] =  url_for('home_focad')
        session['path'] = os.path.join("acompanamiento")
        session['report'] = 33
        session['required_files'] = ['focad.xlsx']
        session['download_file'] =  ['focad.xlsx']
        session['path_template'] =  'acompanamiento/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/42612735-90c1-417e-9c02-078ff1a2a7f2/page/p_md4y6ft88c'
        session['table'] = 'acmp_3' 
        session['servicio'] = 'focad'
        session['file'] = 'focad.xlsx'
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        # Fecha:
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        df_dates = ModelUser.get_distinct_V2(db,  "acmp_3")
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# acompanamiento_catedra:
@app.route('/catedra')
@login_required
def home_catedra():
    if session['rol'] == '3':
        session['back_url'] = url_for('home_catedra')
        session['path'] = os.path.join("acompanamiento")
        session['report'] = 34
        session['required_files'] = ['catedra.xlsx']
        session['download_file'] =  ['catedra.xlsx']
        session['path_template'] =  'acompanamiento/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/64570eca-4cde-4244-ad9b-a51b19c8f8ab/page/p_erp7w9t88c'
        session['table'] = 'acmp_4' 
        session['servicio'] = 'catedra'
        session['file'] = 'catedra.xlsx'
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        # Fecha:
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        
        df_dates = ModelUser.get_distinct_V2(db,  "acmp_4")
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# acompanamiento_tut_geas:
@app.route('/tutgeas')
@login_required
def home_tutorias_y_geas():
    if session['rol'] == '3':
        session['back_url'] = url_for('home_tutorias_y_geas')
        session['path'] = os.path.join("acompanamiento")
        session['report'] = 35
        session['required_files'] = ['geas_tutorias.xlsx']
        session['download_file'] =  ['geas_tutorias.xlsx']
        session['path_template'] =  'acompanamiento/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/8e7cb7fe-0e13-4346-9981-fd0c89167847/page/p_xevbmru88c'
        session['table'] = 'acmp_5'
        session['servicio'] = 'tutorias_y_geas'
        session['file'] = 'geas_tutorias.xlsx'
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        # Fecha:
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        
        
        df_dates = ModelUser.get_distinct_V2(db,  "acmp_5")
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# ESPA:
@app.route('/espa')
@login_required
def home_espa():
    if session['rol'] == '3':
        session['back_url'] = url_for('home_espa')
        session['path'] = os.path.join("acompanamiento")
        session['report'] = 36
        session['required_files'] = ['espa.xlsx']
        session['download_file'] =  ['espa.xlsx']
        session['path_template'] =  'acompanamiento/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/96a83c30-e2e7-4f0c-9b4b-cb3c759f0f67/page/p_8qbh5yu88c'
        session['table'] = 'acmp_6' 
        # Ayuda:
        session['servicio'] = 'espa'
        session['file'] = 'espa.xlsx'
        
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        # Fecha:
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        # get user and date from db:
        # get user and date from db:
        df_dates = ModelUser.get_distinct_V2(db,  "acmp_6")
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')


# UTP:
@app.route('/utp')
@login_required
def home_utp():
    if session['rol'] == '3':
        session['back_url'] = url_for('home_utp')
        session['path'] = os.path.join("acompanamiento")
        session['report'] = 37
        session['required_files'] = ['utp.xlsx']
        session['download_file'] =  ['utp.xlsx']
        session['path_template'] =  'acompanamiento/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/06546943-1f63-4415-8b31-7712dd244fda/page/p_yy69t4li8c'
        session['table'] = 'acmp_7' 
        # Ayuda:
        session['servicio'] = 'utp'
        session['file'] = 'utp.xlsx'
        
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        # Fecha:
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        # get user and date from db:
        # get user and date from db:
        df_dates = ModelUser.get_distinct_V2(db,  "acmp_7")
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')


# ============================================================================
# STEM:
# ============================================================================
@app.route('/home_stem')
@login_required
def home_stem():
    if session['rol'] == '4':
        session['back_url'] = url_for('home_stem')
        return render_template('home_stem.html')
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# stem:
@app.route('/stem_informe_1')
@login_required
def home_stem_informe_1():
    if session['rol'] == '4':
        session['back_url'] = url_for('home_stem_informe_1')
        session['path'] = os.path.join("stem")
        session['report'] = 41
        session['required_files'] = ['datos_capacitaciones_stem.xlsx', 'datos_manuales_stem.xlsx', 'datos_form_stem.xlsx']
        session['download_file'] =  ['stem.xlsx']
        session['path_template'] =  'stem/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/66aeb297-914e-4b37-9ae0-1d116433ab90/page/p_izgj29srcd'
        session['table'] = "stem_3" # table SQL
        session['servicio'] = 'stem_servicios'
        session['file'] = 'stem.xlsx'
        id = session['id']
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        df_dates = ModelUser.get_distinct_V2(db, session['table'] ) # table SQL
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# ============================================================================
# PSL:
# ============================================================================
@app.route('/home_psl')
@login_required
def home_psl():
    if session['rol'] == '5':
        session['back_url'] = url_for('home_psl')
        return render_template('home_psl.html')
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# psl_taller_intracatedra:
@app.route('/taller_intracatedra')
@login_required
def home_taller_intracatedra():
    if session['rol'] == '5':
        session['back_url'] = url_for('home_taller_intracatedra')
        session['path'] = os.path.join("psl")
        session['report'] = 51
        session['required_files'] = ['taller_intracatedra.xlsx']
        session['download_file'] =  ['taller_intracatedra.xlsx']

        session['path_template'] =  'psl/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/c14f20a8-4b67-4809-b58c-63723ef6ef93/page/p_kk6pokq38c'
        session['table'] = 'psl_1'

        
        session['servicio'] = 'Taller intracatedra'
        session['file'] = 'taller_intracatedra.xlsx'
        id = session['id']
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        
        
        
        df_dates = ModelUser.get_distinct_V2(db,  "psl_1")
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# psl_actividades_voluntarias:
@app.route('/actividades_voluntarias')
@login_required
def home_actividades_voluntarias():
    if session['rol'] == '5':
        session['back_url'] = url_for('home_actividades_voluntarias')
        session['path'] = os.path.join("psl")
        session['report'] = 52
        session['required_files'] = ['actividades_voluntarias.xlsx']
        session['download_file'] =  ['actividades_voluntarias.xlsx']

        session['path_template'] =  'psl/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/aab6b809-6c57-42ca-a659-d716d0305431/page/p_a132dfui8c'
        session['table'] = 'psl_2'

        session['servicio'] = 'Actividades voluntarias'
        session['file'] = 'actividades_voluntarias.xlsx'
        id = session['id']
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        
        
        df_dates = ModelUser.get_distinct_V2(db,  "psl_2")
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# ============================================================================
# SEDE MANIZALES
# ============================================================================
# HOME:
@app.route('/home_sede')
@login_required
def home_sede():
    if session['rol'] == '10':
        session['back_url'] = url_for('home_sede')
        return render_template('home_sede.html')
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

    
# sede - matriculados
@app.route('/home_sede_matriculados')
@login_required
def home_sede_matriculados():
    if session['rol'] == '10':
        session['back_url'] = url_for('home_sede_matriculados')
        session['path'] =  os.path.join("sede")
        session['report'] = 101
        session['required_files'] = ['RE_ACT_PER_TABLA_DE_DATOS.xlsx',
                                     'RE_MAT_PAV_PAP_TABLA_DE_DATOS.xlsx',
                                     'RE_MAT_PER_TABLA_DE_DATOS.xlsx']
        session['download_file'] =  ['sede_manizales_matriculados' + '.xlsx']

        session['path_template'] =  'sede/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/57e45d51-13a7-4292-af97-d94af2ede99a/page/p_bkke747r7c'
        session['table'] = 'sede_1'

        session['servicio'] = 'Reporte Matriculados'
        session['file'] = 'sede_manizales_matriculados' + '.xlsx'
        id = session['id']
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        
        # Acá la logica es que los tres reportes se hacen ... hay que hacer varios servicios acá... hay que hacer tres.
        
        df_dates = ModelUser.get_distinct_V2(db,  session['table'])
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')


# sede - Bloq causas administrativas
@app.route('/home_sede_bloq_admin')
@login_required
def home_sede_bloq_admin():
    if session['rol'] == '10':
        session['back_url'] = url_for('home_sede_bloq_admin')
        session['path'] =  os.path.join("sede")
        session['report'] = 102
        session['required_files'] = ['RE_ACT_PER_TABLA_DE_DATOS.xlsx',
                                     'BLQ_Causas_Administrativas_RE_EST_BLQ_PER_TABLA_DE_DATOS.xlsx']
        session['download_file'] =  ['sede_manizales' + '.xlsx']

        session['path_template'] =  'sede/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/57e45d51-13a7-4292-af97-d94af2ede99a/page/p_bkke747r7c'
        session['table'] = 'sede_2'

        session['servicio'] = 'Reporte Bloqueados casusas administrativas'
        session['file'] = 'sede_manizales' + '.xlsx'
        id = session['id']
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de \n \n" + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        
        # Acá la logica es que los tres reportes se hacen ... hay que hacer varios servicios acá... hay que hacer tres.
        
        df_dates = ModelUser.get_distinct_V2(db,  session['table'])
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')
    
    
# sede - Bloq causas academicas
@app.route('/home_sede_bloq_academ')
@login_required
def home_sede_bloq_academ():
    if session['rol'] == '10':
        session['back_url'] = url_for('home_sede_bloq_academ')
        session['path'] =  os.path.join("sede")
        session['report'] = 103
        session['required_files'] = ['RE_ACT_PER_TABLA_DE_DATOS.xlsx',
                                    'RE_MAT_PAV_PAP_TABLA_DE_DATOS.xlsx',
                                    'RE_MAT_PER_TABLA_DE_DATOS.xlsx',
                                    'BLQ_Causas_Academicas_RE_EST_BLQ_PER_TABLA_DE_DATOS.xlsx']
        session['download_file'] =  ['sede_manizales' + '.xlsx']

        session['path_template'] =  'sede/home_acmp_user.html'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/57e45d51-13a7-4292-af97-d94af2ede99a/page/p_bkke747r7c'
        session['table'] = 'sede_3'

        session['servicio'] = 'Reporte Bloqueados casusas academicas'
        session['file'] = 'sede_manizales' + '.xlsx'
        id = session['id']
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        
        # Acá la logica es que los tres reportes se hacen ... hay que hacer varios servicios acá... hay que hacer tres.
        
        df_dates = ModelUser.get_distinct_V2(db,  session['table'])
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')



# ============================================================================
# UNAL EN LA REGION:
# ============================================================================

# HOME:
@app.route('/home_bot_IA')
@login_required
def home_bot_IA():
    if session['rol'] == '9':
        session['back_url'] = url_for('home_bot_IA')
        return render_template('home_bot_IA.html')
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# acompanamiento_unal_lee:
@app.route('/bot_IA_analitica')
@login_required
def home_bot_IA_analitica():
    if session['rol'] == '9':
        session['back_url'] = url_for('home_bot_IA')
        session['path'] = os.path.join("bot_IA")
        session['report'] = 91
        session['required_files'] = ['bot_IA.xlsx']
        session['download_file'] =  ['bot_IA.xlsx']
        session['path_template'] =  'bot_IA/home_acmp_user.html'
        session['servicio'] = 'bot_IA'
        session['file'] = 'bot_IA.xlsx'
        session['link'] = 'https://datastudio.google.com/embed/reporting/c01913f2-743f-4b8f-84cf-10a5c0fee398/page/p_0gycj7kj2c'
        session['table'] = 'bot_IA_1' 
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        # Fecha:
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        # get user and date from db:
        df_dates = ModelUser.get_distinct_V2(db,  "acmp_1") # poner el nombre de la tabla adecuada
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')
    
# acompanamiento_unal_lee:
@app.route('/generar_consulta_IA',methods=['POST'])
@login_required
def generar_consulta_IA():
    if request.method == "POST":
        text = request.form["holatarea"]
        print(text)
        # CONTINUAR: https://blog.futuresmart.ai/mastering-natural-language-to-sql-with-langchain-nl2sql
        return json.dumps({'status':'OK'})





# ============================================================================
# AUTOEVAL:
# ============================================================================
# HOME:
@app.route('/home_autoeval')
@login_required
def home_autoeval():
    if session['rol'] == '11':
        session['back_url'] = url_for('home_autoeval')
        return render_template('home_autoeval.html')
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')

# autoevaluacion::
@app.route('/home_autoeval_analitica')
@login_required
def home_autoeval_analitica():
    if session['rol'] == '11':
        session['back_url'] = url_for('home_autoeval_analitica')
        session['path'] = os.path.join("autoeval")
        session['report'] = 111
        session['required_files'] = ['autoeval.xlsx']
        session['download_file'] =  ['autoeval.xlsx']
        session['path_template'] =  'autoeval/home_acmp_user.html'
        session['servicio'] = 'autoeval'
        session['file'] = 'autoeval.xlsx'
        session['link'] = 'https://lookerstudio.google.com/embed/reporting/0cc62520-898b-4c05-88bf-f113478af848/page/p_3gq3hfnr8c'
        session['table'] = 'autoeval_1' 
        # Ayuda:
        session['msjhelp1'] = "El archivo (o archivos) de subida debe tener el nombre de " + " ".join(session['required_files'])
        session['msjhelp2'] = "Este boton permite generar el reporte. Recuerda que la información en el dash board se actualiza automaticamente cada 15 min."
        session['msjhelp3'] = "Este boton permite descargar en formato excel el reporte generado."
        # Fecha:
        id = session['id']
        date = ModelUser.get_date_modf(db, str(id))
        if date == None:
            date = ''
        session['msj_actualizacion'] = "Ultima actualización de datos:  " + date # get actual modfificacion
        # get user and date from db:
        df_dates = ModelUser.get_distinct_V2(db,  "autoeval_1") # poner el nombre de la tabla adecuada
        data = df_dates.values.tolist()
        # render
        session['data'] = data
        template = render_informe(app.config['UPLOAD_FOLDER'],session)
        return template
    else:
        flash("No tienes acceso.")
        return render_template('auth/login.html')


# ============================================================================
# SUBIR, GENERAR, DESCARGAR
# ============================================================================

# SUBIR:
@app.route('/subir', methods=['POST'])
@login_required
def upload():
    try:
        # Cargar rango para caso psl -> extraer información de hojas de excel.
        session['rango_psl'] = request.form["miInput"]
    except:
        pass
    
    try:
        session["periodoReporte"] = request.form["periodoReporte"]
    except:
        pass

    uploaded_files = request.files.getlist("file[]") # Archivos.
    if len(uploaded_files) == 1 and  uploaded_files[0].filename == '':
        flash('No has seleccionado un archivo')
        return redirect(session['back_url']) # pagina anterior
    
    # Este caso particular sucede para generar reporte 24 -> corregir, porque no puede ser
    # particularizado en esta parte.
    # No comprobar el reporte 52 de actividades voluntarias, mientras se definen
    # los nombres que quedaran por defecto.
    print("=====================================================")
    print(session['report'] != 52)
    if not(session['report'] == 24) and not(session['report'] == 52):
        print("SI ENTRE")
        file_names_upload = [file_u.filename  for file_u in uploaded_files]
        list_check = [file in file_names_upload for file in session['required_files']]
        for file in session['required_files']:
            print(file_names_upload)
            print(file, file in file_names_upload)
        print("=====================================================")
        print(list_check)
        tf_upload = all(list_check)
        #tf_upload = True
        if tf_upload == False:
            flash('Nombre de archivo incorrecto')
            return redirect(session['back_url']) # pagina anterior
    filenames = []
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = session['path']
            # Excluir psl actividades voluntarias
            if session["report"] != 52:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],path,'subidos',filename))
            else:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],path,'subidos','actividades_voluntarias',filename))
            filenames.append(filename)
        else:
            flash(f'El archivo {file.filename} tiene una extension no permitida.')
    flash("Archivos subidos adecuadamente")
    # This line is essential, store the data in session
    session['filenames'] = filenames
    #return render_template('upload.html', filenames=filenames)
    return redirect(session['back_url'])

# GENERAR:
@app.route('/generar', methods=['POST'])
@login_required
def generar():
    if request.method == "POST":
        print(f"Se esta ejecutando generar con el reporte = { session['report'] }")
        try: 
            # ADMIN ========================================================================:
            if session['report'] == 1:
                # Archivos Requeridos:
                name_pss = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
                name_estudiantes_ant = os.path.join('admin','admin_reportes_generales','subidos','Matriculados_Informacion_Basica_ant.xlsx')
                name_estudiantes_now = os.path.join('admin','admin_reportes_generales','subidos','Matriculados_Informacion_Basica_presente.xlsx')
                name_asig = os.path.join('admin','admin_reportes_generales','subidos','Inscripcion_de_asignaturas.xlsx')
                name_matr_pp = os.path.join('admin','admin_reportes_generales','subidos','Matriculados_por_periodo.xlsx')
                list_names = [name_asig, name_matr_pp]
                # Guardar:
                name_save = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
                # outputs:
                df_admin_1 = MODEL_ADMIN.main_siaspp2(name_pss, name_estudiantes_ant, name_estudiantes_now, list_names, name_save, periodo='2022-2S')
                # to google:
                #try:
                #    MODEL_ADMIN.write_google_sheet(df_admin_1, 'servicio', 'REPORTES_DAMA', 'ADMIN_1',w=1)
                #except:
                #    MODEL_ADMIN.write_google_sheet(df_admin_1, 'servicio', 'REPORTES_DAMA', 'ADMIN_1',w=0)
                # flask mensaje
                flash('Cruce Realizado.')
                # Actualizar fecha de modificacion:
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                return json.dumps({'status':'OK'})
            
  
            # SIA =============================================================================:
            # matriculados
            if session['report'] == 21:
                # Archivos requeridos:
                name_estudiantes_now = os.path.join('sia','subidos','Matriculados_Informacion_Basica_ant.xlsx')
                name_estudiantes_ant = os.path.join('sia','subidos','Matriculados_Informacion_Basica_presente.xlsx')
                name_matr_pp = os.path.join('sia','subidos','Matriculados_por_periodo.xlsx')
                name_asignaturas = os.path.join('sia','subidos','Inscripcion_de_asignaturas.xlsx')
                name_matr_ib = os.path.join('sia','subidos','Matriculados_Informacion_Basica.xlsx')
                # periodo de reporte:
                periodo = request.form["periodo"] # poner form en html
                # save
                name_save = os.path.join('sia','generados','matriculados.xlsx')
                # df historico:
                df_historico = MODEL_SERVICIOS.get_google_sheet('sia', 'matriculados', 'principal')
                # df:
                df = MODEL_SIA.main_matriculados(name_asignaturas, name_estudiantes_now, name_estudiantes_ant, name_matr_ib, name_matr_pp, name_save, periodo, df_historico)
                # to google:
                MODEL_SIA.write_google_sheet(df, 'sia', 'matriculados', 'principal')
                # mensaje flash:
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                return json.dumps({'status':'OK'})
            
            # estadisticas:
            if session['report'] == 22:
                # Archivos requeridos:
                name_sia_grphor = os.path.join('sia','subidos','horarios_y_grupos.xlsx')
                name_sia_asignaturas = os.path.join('sia','subidos','asignaturas_inscritas.xlsx')
                # periodo de generacion del informe:
                periodo = request.form["periodo"] # poner form en html
                # save
                name_save = os.path.join('sia','generados','estadisticas.xlsx')
                # df historico:
                #df_historico = MODEL_SERVICIOS.get_google_sheet('sia', 'matriculados', 'principal')
                # df:
                df_1 = MODEL_SIA.estadisticas_1(name_sia_grphor)
                # proceso de guardad:
                df_pre_nuevos, df_pre_antiguos = MODEL_SIA.inscritos_nivel(name_sia_asignaturas, 'PREGRADO', periodo)
                df_pos_nuevos, df_pos_antiguos = MODEL_SIA.inscritos_nivel(name_sia_asignaturas, 'POSGRADO', periodo)
                # to google:
                MODEL_SIA.write_google_sheet(df_1, 'sia', 'estadisticas', 'asignaturas')
                MODEL_SIA.write_google_sheet(df_pre_nuevos, 'sia', 'estadisticas', 'ADMITIDOS PREGRADO')
                MODEL_SIA.write_google_sheet(df_pre_antiguos, 'sia', 'estadisticas', 'ANTIGUOS PREGRADO')
                MODEL_SIA.write_google_sheet(df_pos_nuevos, 'sia', 'estadisticas', 'ADMITIDOS POSGRADO')
                MODEL_SIA.write_google_sheet(df_pos_antiguos, 'sia', 'estadisticas', 'ANTIGUOS POSGRADO')
                # save excel
                list_dfs = [
                    (df_1, 'asignaturas'),
                    (df_pre_nuevos, 'ADMITIDOS PREGRADO'),
                    (df_pre_antiguos,'ANTIGUOS PREGRADO'),
                    (df_pos_nuevos, 'ADMITIDOS POSGRADO'),
                    (df_pos_antiguos,'ANTIGUOS POSGRADO')
                    ]
                MODEL_SIA.write_engine(list_dfs, name_save)
                # mensaje flash:
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                return json.dumps({'status':'OK'})
            
            # proyecto de grado y tesis:    
            if session['report'] == 23:
                # Archivos requeridos:
                name_sia_grphor = os.path.join('sia','subidos','horarios_y_grupos.xlsx')
                name_sia_asignaturas = os.path.join('sia','subidos','asignaturas_inscritas.xlsx')
                # save:
                name_save = os.path.join('sia','generados','proyectos_y_tesis.xlsx')
                # df:
                df = MODEL_SIA.proyectos_tesis(name_sia_asignaturas, name_sia_grphor, name_save)
                # to google:
                MODEL_SIA.write_google_sheet(df, 'sia', 'Proyectos_tesis', 'Principal')
                # mensaje flash:
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                return json.dumps({'status':'OK'})    
            
             # tutores:
            
            # tutores:
            if session['report'] == 24:
                # Archivos requeridos:
                name_tutores = os.path.join('sia','subidos','tutores.xlsx')
                name_matriculados = os.path.join('sia','subidos','Matriculados_Informacion_Basica_presente_tutores.xlsx')
                # save:
                name_save = os.path.join('sia','generados','tutores.xlsx')
                # df:
                df_list, df_todo = MODEL_SIA.tutores(name_tutores, name_save, name_matriculados)
                # to google:
                list_dfs = []
                for df, nombre in df_list:
                    list_dfs.append((df,nombre))
                    time.sleep(2.4)
                    try:
                        MODEL_SIA.write_google_sheet(df, 'sia', 'tutores', nombre, w=0)
                    except:
                        MODEL_SIA.write_google_sheet(df, 'sia', 'tutores', nombre, w=1)
                # todo
                try:
                    MODEL_SIA.write_google_sheet(df_todo, 'sia', 'tutores', 'TODO', w=0)
                except:
                    MODEL_SIA.write_google_sheet(df_todo, 'sia', 'tutores', 'TODO', w=1)
                
                # to excel:
                list_dfs.append((df_todo,'TODO'))
                MODEL_SIA.write_engine(list_dfs, name_save)
                # mensaje flash
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                return json.dumps({'status':'OK'})
            
            
            # ACOMPAÑAMIENTO=============================================================:
            # unal lee
            if session['report'] == 31: 
                # Archivos Requeridos:
                name_load = os.path.join('acompanamiento','subidos','unal_lee.xlsx')
                name_save = os.path.join('acompanamiento','generados', 'unal_lee.xlsx')
                # Desde admin:
                name_pss = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
                name_pss2 = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
                # Historico....
                #df_historico = MODEL_SERVICIOS.get_google_sheet('servicio', 'REPORTES_DAMA', 'ACMP_1')
                #df_historico = ModelUser.get_all_table(db, "acmp_1")
                df_historico = ModelUser.get_all_table(db, session["table"])
                #df_historico = pd.DataFrame()
                print('HISTORICO ==================================================')
                print(len(df_historico))
                # DF:
                df_ppl, df = MODEL_SERVICIOS.make_service2pss(name_pss, name_load, name_pss2, name_save, df_historico)
                # cambiar modulo servicios de aca para abajo.
                MODEL_SERVICIOS.write_google_sheet(df, 'servicio', my_config_constants['name_file_gsheet_servicios_dama'], session['table'])
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_ppl["DATE_UPDATE"] = date_time
                df_ppl["USER"] = session['username']
                # QUITAR UNAMED
                msj = ModelUser.upload_df(db, df_ppl, "acmp_1")
                return json.dumps({'status':'OK'})
            
            # tramites
            if session['report'] == 32:
                # Archivos Requeridos:
                name_load = os.path.join('acompanamiento','subidos','tramites_solicitudes.xlsx')
                name_save = os.path.join('acompanamiento','generados', 'tramites_solicitudes.xlsx')
                # Desde admin:
                name_pss = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
                name_pss2 = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
                # Historico....
                #df_historico = MODEL_SERVICIOS.get_google_sheet('servicio', 'REPORTES_DAMA', 'ACMP_1')
                #df_historico = ModelUser.get_all_table(db, "acmp_1")
                df_historico = ModelUser.get_all_table(db, session["table"])
                print('HISTORICO ==================================================')
                print(len(df_historico))
                # DF:
                df_ppl, df = MODEL_SERVICIOS.make_service2pss(name_pss, name_load, name_pss2, name_save, df_historico)
                # cambiar modulo servicios de aca para abajo.
                MODEL_SERVICIOS.write_google_sheet(df, 'servicio', my_config_constants['name_file_gsheet_servicios_dama'], session['table'])
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_ppl["DATE_UPDATE"] = date_time
                df_ppl["USER"] = session['username']
                msj = ModelUser.upload_df(db, df_ppl, "acmp_2")
                return json.dumps({'status':'OK'})

            # focad:
            if session['report'] == 33:
                # Archivos Requeridos:
                name_load = os.path.join('acompanamiento','subidos','focad.xlsx')
                # save
                name_save = os.path.join('acompanamiento','generados', 'focad.xlsx')
                # Desde admin:
                name_pss = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
                name_pss2 = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
                # Historico....
                #df_historico = MODEL_SERVICIOS.get_google_sheet('servicio', 'REPORTES_DAMA', 'ACMP_1')
                #df_historico = ModelUser.get_all_table(db, "acmp_1")
                df_historico = ModelUser.get_all_table(db, session["table"])
                print('HISTORICO ==================================================')
                print(len(df_historico))
                # DF:
                df_ppl, df = MODEL_SERVICIOS.make_service2pss(name_pss, name_load, name_pss2, name_save, df_historico)
                # cambiar modulo servicios de aca para abajo.
                MODEL_SERVICIOS.write_google_sheet(df, 'servicio', my_config_constants['name_file_gsheet_servicios_dama'], session['table'])
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_ppl["DATE_UPDATE"] = date_time
                df_ppl["USER"] = session['username']
                msj = ModelUser.upload_df(db, df_ppl, "acmp_3")
                return json.dumps({'status':'OK'})
            
                        # catedra:
            
            # catedra
            if session['report'] == 34:
                # catedra.xlsx
                # Archivos Requeridos:
                name_load = os.path.join('acompanamiento','subidos','catedra.xlsx')
                # save
                name_save = os.path.join('acompanamiento','generados', 'catedra.xlsx')
                # Desde admin:
                name_pss = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
                name_pss2 = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
                # Historico....
                #df_historico = MODEL_SERVICIOS.get_google_sheet('servicio', 'REPORTES_DAMA', 'ACMP_1')
                #df_historico = ModelUser.get_all_table(db, "acmp_1")
                df_historico = ModelUser.get_all_table(db, session["table"])
                print('HISTORICO ==================================================')
                print(len(df_historico))
                # DF:
                df_ppl, df = MODEL_SERVICIOS.make_service2pss(name_pss, name_load, name_pss2, name_save, df_historico)
                # cambiar modulo servicios de aca para abajo.
                MODEL_SERVICIOS.write_google_sheet(df, 'servicio', my_config_constants['name_file_gsheet_servicios_dama'], session['table'])
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_ppl["DATE_UPDATE"] = date_time
                df_ppl["USER"] = session['username']
                msj = ModelUser.upload_df(db, df_ppl, "acmp_4")
                return json.dumps({'status':'OK'})
            
            # geas y tutorias:
            if session['report'] == 35: # geas y tutorias
                # geas_tutorias.xlsx
                # Archivos Requeridos:
                name_load = os.path.join('acompanamiento','subidos','geas_tutorias.xlsx')
                name_save = os.path.join('acompanamiento','generados', 'geas_tutorias.xlsx')
                # Desde admin:
                name_pss = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
                name_pss2 = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
                # Historico....
                #df_historico = MODEL_SERVICIOS.get_google_sheet('servicio', 'REPORTES_DAMA', 'ACMP_1')
                #df_historico = ModelUser.get_all_table(db, "acmp_1")
                df_historico = ModelUser.get_all_table(db, session["table"])
                print('HISTORICO ==================================================')
                print(len(df_historico))
                # DF:
                df_ppl, df = MODEL_SERVICIOS.make_service2pss(name_pss, name_load, name_pss2, name_save, df_historico)
                # cambiar modulo servicios de aca para abajo.
                MODEL_SERVICIOS.write_google_sheet(df, 'servicio', my_config_constants['name_file_gsheet_servicios_dama'], session['table'])
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_ppl["DATE_UPDATE"] = date_time
                df_ppl["USER"] = session['username']
                msj = ModelUser.upload_df(db, df_ppl, "acmp_5")
                
                return json.dumps({'status':'OK'})

                        # ESPA:
            
            # Espa
            if session['report'] == 36: # ESPA
                # geas_tutorias.xlsx
                # Archivos Requeridos:
                name_load = os.path.join('acompanamiento','subidos','espa.xlsx')
                name_save = os.path.join('acompanamiento','generados', 'espa.xlsx')
                # Desde admin:
                name_pss = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
                name_pss2 = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
                # Historico....
                #df_historico = MODEL_SERVICIOS.get_google_sheet('servicio', 'REPORTES_DAMA', 'ACMP_1')
                #df_historico = ModelUser.get_all_table(db, "acmp_1")
                df_historico = ModelUser.get_all_table(db, session["table"])
                print('HISTORICO ==================================================')
                print(len(df_historico))
                # DF:
                df_ppl, df = MODEL_SERVICIOS.make_service2pss(name_pss, name_load, name_pss2, name_save, df_historico)
                # cambiar modulo servicios de aca para abajo.
                MODEL_SERVICIOS.write_google_sheet(df, 'servicio', my_config_constants['name_file_gsheet_servicios_dama'], session['table'])
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_ppl["DATE_UPDATE"] = date_time
                df_ppl["USER"] = session['username']
                msj = ModelUser.upload_df(db, df_ppl, "acmp_6")
                
                return json.dumps({'status':'OK'})

            # UTP:
            if session['report'] == 37: # UTP
                # UTP.xlsx
                # Archivos Requeridos:
                name_load = os.path.join('acompanamiento','subidos','utp.xlsx')
                name_save = os.path.join('acompanamiento','generados', 'utp.xlsx')
                # Desde admin:
                name_pss = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
                name_pss2 = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
                # Historico....
                #df_historico = MODEL_SERVICIOS.get_google_sheet('servicio', 'REPORTES_DAMA', 'ACMP_1')
                #df_historico = ModelUser.get_all_table(db, "acmp_1")
                df_historico = ModelUser.get_all_table(db, session["table"])
                print('HISTORICO ==================================================')
                print(len(df_historico))
                # DF:
                df_ppl, df = MODEL_SERVICIOS.make_serviceUTP(name_pss, name_load, name_pss2, name_save, df_historico)
                # cambiar modulo servicios de aca para abajo.
                MODEL_SERVICIOS.write_google_sheet(df, 'servicio', my_config_constants['name_file_gsheet_servicios_dama'], session['table'])
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_ppl["DATE_UPDATE"] = date_time
                df_ppl["USER"] = session['username']
                msj = ModelUser.upload_df(db, df_ppl, "acmp_7")
                
                return json.dumps({'status':'OK'})
        
            
            # PSL =================================================================:
            

            # actividades voluntarias:
            if session['report'] == 52:
                # Archivos Requeridos:
                #name_load = os.path.join('psl','subidos','actividades_voluntarias.xlsx')
                name_load = os.path.join('psl','subidos')
                name_save = os.path.join('psl','generados', 'actividades_voluntarias.xlsx')
                # Desde admin:
                name_pss = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
                name_pss2 = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
                # Historico....
                #df_historico = MODEL_SERVICIOS.get_google_sheet('servicio', 'REPORTES_DAMA', 'ACMP_1')
                #df_historico = ModelUser.get_all_table(db, "acmp_1")
                df_historico = ModelUser.get_all_table(db, session["table"])
                print('HISTORICO ==================================================')
                print(len(df_historico))
                # DF:
                rangos = session["rango_psl"]
                lista_de_cadenas = ast.literal_eval(rangos)
                path_load = os.path.join("src","data","psl","subidos","actividades_voluntarias")
                df_salida = asistenciaOriginal_to_estandar_AV(path_load, lista_de_cadenas)
                print("=============================ANTES DE HACER MAKE SERVIICE================")
                print(df_salida.info())
                df_ppl, df = MODEL_SERVICIOS.make_service2pss(name_pss, name_load, name_pss2, name_save, df_historico, df_salida)
                df_ppl = df_ppl.drop(columns=["index"])
                df_ppl= df_ppl.filter(regex='^(?!Unnamed:).', axis=1)

                df = df.drop(columns=["index"])
                df = df.filter(regex='^(?!Unnamed:).', axis=1)

                # cambiar modulo servicios de aca para abajo.
                print("====== ANTES DE ESCRIBIR ===================")
                print(df.info())
                MODEL_SERVICIOS.write_google_sheet(df, 'servicio', my_config_constants['name_file_gsheet_servicios_dama'], session['table'])
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_ppl["DATE_UPDATE"] = date_time
                df_ppl["USER"] = session['username']
                # Porque pasa esto ? -> Se necesita quitar el index:
                
                print("====== ANTES DE ESCRIBIR ===================")
                print(df_ppl.info())
                msj = ModelUser.upload_df(db, df_ppl, "psl_2")
                return json.dumps({'status':'OK'})
            
            
            # SEDE =================================================================:
                    # matriculados:
            if session['report'] == 101: 
               
                # Cargar datos historicos:
                df_historico = ModelUser.get_all_table(db, session["table"], report='delete_sede')
                # Mostrar información de historico en consola:
                print('HISTORICO ==================================================')
                print(len(df_historico))
                # Obtener el periodo:
                Rep = session["periodoReporte"]
                # Mostrar:
                print(Rep)
                # Paths informes estaticos:
                PATH_PRINCIPAL_2 = my_config_constants["path_principal_2"]
                name_activos2 = os.path.join('FACULTADES_MAIN_2022_2S.xlsx')
                name_bloq_admin = os.path.join('FACULTADES_BLOQUEADOS_ADMINISTRATIVAS.xlsx')
                name_bloq_academ = os.path.join('FACULTADES_BLOQUEADOS_ACADEMICAS.xlsx')
                name_planes = os.path.join('Planes.xlsx')
                # Pre proceso de datos estaticos:
                col_out_main, _, _, df_planes = inicializador_cols(PATH_PRINCIPAL_2, name_activos2, name_bloq_admin,
                                                                   name_bloq_academ, name_planes)
                # Archivos necesarios para reporte: Matriculados:
                name_activos = os.path.join('RE_ACT_PER_TABLA_DE_DATOS.xlsx')
                name_pav_pap = os.path.join('RE_MAT_PAV_PAP_TABLA_DE_DATOS.xlsx')
                name_mat_per = os.path.join('RE_MAT_PER_TABLA_DE_DATOS.xlsx')
                name_est_bloq = None
                name_matr_ant = None
                # Carga de archivos:
                df_activos, df_pav_pap, df_mat_per, _, _ = load_data_sede(name_activos, name_pav_pap, name_mat_per, name_est_bloq, name_matr_ant)
                # Preprocesamiento de dfs: Matriculados:
                df_planes, df_activos_discap, df_pav_pap_v2, df_mat_per_v2 = preprocessing_sede(df_planes, df_activos, 
                                                                                                    df_pav_pap, df_mat_per)
                # Hacer reporte: Matriculados:
                df_matriculados = main_matriculados(df_pav_pap_v2, df_mat_per_v2, df_planes,
                                                            df_activos_discap, col_out_main, periodo = Rep)
                # Concatenar:
                df_final = pd.concat([df_historico, df_matriculados])
                # Formato de columnas:
                cols_gsh = ["AVANCE_CARRERA",
                            "FACULTAD",
                            "PLAN",
                            "TIPO_NIVEL",
                            "EDAD",
                            "SEXO",
                            "DEPARTAMENTO_PROCEDENCIA",
                            "ESTRATO",
                            "PBM",
                            "MATRICULAS",
                            "PAPA",
                            "hashed_ID",
                            "NIVEL_2",
                            "DISCAPACIDAD",
                            "AVANCE_HISTOGRAMA",
                            "PERIODO_REPORTE",
                            "SUBACCESO",
                            "ID",
                            "NOMBRES",
                            "APELLIDO1",
                            "CORREO"]
                # Check repetidos entre: df_final.
                df_matriculados_def = check_repeat_main(df_final, cols_gsh)
                
                # save reporte:
                path_save = my_config_constants["path_save_sede"]
                path_save = os.path.join(path_save, session['download_file'][0])
                df_matriculados_def.to_excel(path_save, index=False)
                
                # Cast df:
                df_matriculados_def = format_column(df_matriculados_def, "PBM", "to_int")
                df_matriculados_def = format_column(df_matriculados_def, "EDAD", "to_int")
                df_matriculados_def = format_column(df_matriculados_def, "MATRICULAS", "to_int")
                
                df_matriculados_def = format_column(df_matriculados_def, "PAPA", "to_float")
                df_matriculados_def = format_column(df_matriculados_def, "AVANCE_CARRERA", "to_float")
                
                # cargar excel
                MODEL_SERVICIOS.write_google_sheet(df_matriculados_def,
                                                   my_config_constants['type_gsheet_write_sede'],
                                                   my_config_constants['name_file_gsheet_sede'],
                                                   session['table']) 
                
                # Seleccionar solo reporte actual luego de quitar repetidos:
                df_matriculados_def = df_matriculados_def[df_matriculados_def["PERIODO_REPORTE"] == Rep]
                # Actualizar excel: 
                """
                #NOTA: hace falta identificar si el ID de reporte y ID de usuario hacen problemas....
                #por ahora todo bien y hay que atacar excel:
                """
                # MODEL_SERVICIOS.write_google_sheet(df_matriculados_def, 'servicio', 'REPORTES_DAMA', 'STEM_1')
                # Mensaje de exito:
                
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_matriculados_def["DATE_UPDATE"] = date_time
                df_matriculados_def["USER"] = session['username']
                # QUITAR UNAMED
                msj = ModelUser.upload_df(db, df_matriculados_def, session['table'])
                return json.dumps({'status':'OK'})
        
            # Bloqueados causas administrativas:
            if session['report'] == 102:
            
                df_historico = ModelUser.get_all_table(db, session["table"], report='delete_sede')
                
                
                print('HISTORICO ==================================================')
                print(len(df_historico))
                
                Rep = session["periodoReporte"]
                # Rep = session["periodoReporte"]
                print(Rep)
                #Rep = "2014-20S"
                
                
                #PATH_PRINCIPAL_2 = "src\data\static_data\sede"
                PATH_PRINCIPAL_2 = my_config_constants["path_principal_2"]
                name_activos2 = os.path.join('FACULTADES_MAIN_2022_2S.xlsx')
                name_bloq_admin = os.path.join('FACULTADES_BLOQUEADOS_ADMINISTRATIVAS.xlsx')
                name_bloq_academ = os.path.join('FACULTADES_BLOQUEADOS_ACADEMICAS.xlsx')
                
                    # from static data:
                name_planes = os.path.join('Planes.xlsx')
                
                col_out_main, col_out_hoja_2, col_out_hoja_3, df_planes = inicializador_cols(PATH_PRINCIPAL_2, name_activos2, name_bloq_admin, name_bloq_academ, name_planes)
                
                
                
                name_activos = os.path.join('RE_ACT_PER_TABLA_DE_DATOS.xlsx')
                name_pav_pap = None
                name_mat_per = None
                # name_est_bloq = os.path.join('upload','2024-1S_BLQ_Causas_Administrativas_RE_EST_BLQ_PER_TABLA DE DATOS_Actualizacion.xlsx')
                name_est_bloq = os.path.join('BLQ_Causas_Administrativas_RE_EST_BLQ_PER_TABLA_DE_DATOS.xlsx')
                name_matr_ant = None
                
                df_activos, df_pav_pap, df_mat_per, df_est_bloq, df_matriculados_ant = load_data_sede(name_activos, name_pav_pap, name_mat_per, name_est_bloq, name_matr_ant)
                
                
                df_pav_pap = None
                df_mat_per = None
                
                
                df_planes, df_activos_discap, df_pav_pap_v2, df_mat_per_v2 = preprocessing_sede(df_planes, df_activos, df_pav_pap, df_mat_per)
                
                df_bloq_main_save  = main_bloq_admin(df_est_bloq, df_activos, df_planes, col_out_hoja_2, periodo = Rep)
                
                
                # concatenar:
                df_final = pd.concat([df_historico, df_bloq_main_save])
                
                cols_gsh = ["BLOQUEO",
                        "FACULTAD",
                        "PLAN",
                        "NIVEL",
                        "AVANCE_CARRERA",
                        "SEXO",
                        "EDAD",
                        "NUMERO_MATRICULAS",
                        "PAPA",
                        "PBM",
                        "ESTRATO",
                        "DEPTO_RESIDENCIA",
                        "DISCAPACIDAD",
                        "hashed_ID",
                        "NIVEL_2",
                        "AVANCE_HISTOGRAMA",
                        "PERIODO_REPORTE",
                        "SUBACCESO",
                        "DOCUMENTO",
                        "NOMBRES",
                        "APELLIDO1",
                        "EMAIL",
                        "ID"]
                    
                df_bloq_administrativas_def = check_repeat_main(df_final, cols_gsh)
                
                # save reporte:
                path_save = my_config_constants["path_save_sede"]
                path_save = os.path.join(path_save, session['download_file'][0])
                df_bloq_administrativas_def.to_excel(path_save, index=False)
                
                print("==================== SALIENDO DE CHECK REPEAT =============================")
                print(df_bloq_administrativas_def.info())
                    
                
                # Formatos:
                df_bloq_administrativas_def['PAPA'] = df_bloq_administrativas_def['PAPA'].apply(lambda x: f"{x}".replace('.', ',') if pd.notnull(x) else "")
                    
                # Cast df:
                df_bloq_administrativas_def = format_column(df_bloq_administrativas_def, "PBM", "to_int")
                df_bloq_administrativas_def = format_column(df_bloq_administrativas_def, "NUMERO_MATRICULAS", "to_int")
                
                df_bloq_administrativas_def = format_column(df_bloq_administrativas_def, "PAPA", "to_float")
                df_bloq_administrativas_def = format_column(df_bloq_administrativas_def, "AVANCE_CARRERA", "to_float")
                    
                MODEL_SERVICIOS.write_google_sheet(df_bloq_administrativas_def,
                                                    my_config_constants['type_gsheet_write_sede'],
                                                    my_config_constants['name_file_gsheet_sede'],
                                                    session['table'])     
                    
                # Seleccionar solo reporte actual luego de quitar repetidos:
                df_bloq_administrativas_def = df_bloq_administrativas_def[df_bloq_administrativas_def["PERIODO_REPORTE"] == Rep]
                
                # Actualizar excel: 
                    
                """
                #NOTA: hace falta identificar si el ID de reporte y ID de usuario hacen problemas....
                #por ahora todo bien y hay que atacar excel:
                """
                
                print("==================== Antes de escribir DE CHECK REPEAT =============================")
                print(df_bloq_administrativas_def.info())
                
                
                
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_bloq_administrativas_def["DATE_UPDATE"] = date_time
                df_bloq_administrativas_def["USER"] = session['username']
                # QUITAR UNAMED
                msj = ModelUser.upload_df(db, df_bloq_administrativas_def, session['table'])
                
                return json.dumps({'status':'OK'})
        
            # Bloqueados causas academicas:
            if session['report'] == 103:
                
                df_historico = ModelUser.get_all_table(db, session["table"], report='delete_sede')
                
                
                print('HISTORICO ==================================================')
                print(len(df_historico))
                
                Rep = session["periodoReporte"]
                # Rep = session["periodoReporte"]
                print(Rep)
                #Rep = "2014-20S"
                
                
                #PATH_PRINCIPAL_2 = "src\data\static_data\sede"
                PATH_PRINCIPAL_2 = my_config_constants["path_principal_2"]
                name_activos2 = os.path.join('FACULTADES_MAIN_2022_2S.xlsx')
                name_bloq_admin = os.path.join('FACULTADES_BLOQUEADOS_ADMINISTRATIVAS.xlsx')
                name_bloq_academ = os.path.join('FACULTADES_BLOQUEADOS_ACADEMICAS.xlsx')
                
                    # from static data:
                name_planes = os.path.join('Planes.xlsx')
                
                col_out_main, col_out_hoja_2, col_out_hoja_3, df_planes = inicializador_cols(PATH_PRINCIPAL_2, name_activos2, name_bloq_admin, name_bloq_academ, name_planes)
                
                
                
                name_activos = os.path.join('RE_ACT_PER_TABLA_DE_DATOS.xlsx')
                name_pav_pap =  os.path.join('RE_MAT_PAV_PAP_TABLA_DE_DATOS.xlsx')
                name_mat_per = os.path.join('RE_MAT_PER_TABLA_DE_DATOS.xlsx')
                name_est_bloq = None
                name_matr_ant = os.path.join('BLQ_Causas_Academicas_RE_EST_BLQ_PER_TABLA_DE_DATOS.xlsx')
                
                
                
                # HAY QUE PONER COMO FILE MATRICULADOS POR PERIODO ojo!
                
                df_activos, df_pav_pap, df_mat_per, df_est_bloq, df_matriculados_ant = load_data_sede(name_activos, name_pav_pap, name_mat_per, name_est_bloq, name_matr_ant)
                
                
                
                df_planes, df_activos_discap, df_pav_pap_v2, df_mat_per_v2 = preprocessing_sede(df_planes, df_activos, df_pav_pap, df_mat_per)
                
                #df_bloq_main_save  = main_bloq_admin(df_est_bloq, df_activos, df_planes, col_out_hoja_2, periodo = Rep)
                
                print("===================SALIDA DE MATRICULADOS DE <preprocessing_sede> : ")
                print(df_mat_per_v2.info())
                
                
                df_bloq_acadm_main_save  = main_bloq_academ(df_pav_pap, df_matriculados_ant, df_planes, df_activos_discap, df_mat_per_v2, col_out_hoja_3, periodo = Rep)
                
                
                # concatenar:
                df_final = pd.concat([df_historico, df_bloq_acadm_main_save])
                
                cols_gsh =  [
                        "FACULTAD",
                        "PLAN",
                        "TIPO_NIVEL",
                        "SEXO",
                        "ESTRATO",
                        "DEPTO_PROCEDENCIA",
                        "NUM_MATRICULAS",
                        "PAPA",
                        "AVANCE_CARRERA",
                        "hashed_ID",
                        "NIVEL_2",
                        "DISCAPACIDAD",
                        "CAUSA_BLOQUEO",
                        "EDAD",
                        "PBM",
                        "AVANCE_HISTOGRAMA",
                        "PERIODO_REPORTE",
                        "SUBACCESO",
                        "DOCUMENTO",
                        "NOMBRES",
                        "APELLIDO1",
                        "EMAIL",
                        "ID"
                    ]
                    
                df_bloq_academicas_def = check_repeat_main(df_final, cols_gsh)
                
                print("==================== SALIENDO DE CHECK REPEAT =============================")
                print(df_bloq_academicas_def.info())
                
                # save reporte:
                path_save = my_config_constants["path_save_sede"]
                path_save = os.path.join(path_save, session['download_file'][0])
                df_bloq_academicas_def.to_excel(path_save, index=False)
                
                # Cast df:
                df_bloq_academicas_def = format_column(df_bloq_academicas_def, "PBM", "to_int")
                df_bloq_academicas_def = format_column( df_bloq_academicas_def, "NUMERO_MATRICULAS", "to_int")
                
                
                df_bloq_academicas_def = format_column(df_bloq_academicas_def, "PAPA", "to_float")
                df_bloq_academicas_def = format_column(df_bloq_academicas_def, "AVANCE_CARRERA", "to_float")
                
                MODEL_SERVICIOS.write_google_sheet(df_bloq_academicas_def,
                                                    my_config_constants['type_gsheet_write_sede'],
                                                    my_config_constants['name_file_gsheet_sede'],
                                                    session['table'])
                    
                # Seleccionar solo reporte actual luego de quitar repetidos:
                df_bloq_academicas_def = df_bloq_academicas_def[df_bloq_academicas_def["PERIODO_REPORTE"] == Rep]
                
                # Actualizar excel: 
                    
                """
                #NOTA: hace falta identificar si el ID de reporte y ID de usuario hacen problemas....
                #por ahora todo bien y hay que atacar excel:
                """
                
                # MODEL_SERVICIOS.write_google_sheet(df_matriculados_def, 'servicio', 'REPORTES_DAMA', 'STEM_1')
                
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_bloq_academicas_def["DATE_UPDATE"] = date_time
                df_bloq_academicas_def["USER"] = session['username']
                # QUITAR UNAMED
                msj = ModelUser.upload_df(db, df_bloq_academicas_def, session['table'])
                
                
                
                return json.dumps({'status':'OK'})
            
        except Exception as e:
            # Obtener el resumen del error
            print("____________________ERROR______________________________")
            print(traceback.format_exc().splitlines())
            error_message = traceback.format_exc().splitlines()[-1]
            flash(f"Hubo un error al realizar el reporte: {error_message}")
            return json.dumps({'status':'OK'})
       
        
                    
        
        # taller intracatedra:
        if session['report'] == 51:
            # Archivos Requeridos:
            name_load = os.path.join('psl','subidos','taller_intracatedra.xlsx')
            name_save = os.path.join('psl','generados', 'taller_intracatedra.xlsx')
            # Desde admin:
            name_pss = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
            name_pss2 = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
            # Historico....
            #df_historico = MODEL_SERVICIOS.get_google_sheet('servicio', 'REPORTES_DAMA', 'ACMP_1')
            #df_historico = ModelUser.get_all_table(db, "acmp_1")
            df_historico = ModelUser.get_all_table(db, session["table"])
            print('HISTORICO ==================================================')
            print(len(df_historico))
            # DF:

            # DF:
            rangos = session["rango_psl"]
            lista_de_cadenas = ast.literal_eval(rangos)
            path_load = os.path.join("'/home/Analisis/basic-flask-app/src/data'","psl","subidos","taller_intracatedra.xlsx")
            df_salida = asistenciaOriginal_to_estandar_TIC(path_load, lista_de_cadenas)

            df_ppl, df = MODEL_SERVICIOS.make_service2pss(name_pss, name_load, name_pss2, name_save, df_historico, df_salida)
            # cambiar modulo servicios de aca para abajo.
            df_ppl = df_ppl.drop(columns=["index"])
            df_ppl= df_ppl.filter(regex='^(?!Unnamed:).', axis=1)

            # estan saliendo con indice y con columnas no nombradas ¿Porque?
            df = df.drop(columns=["index"])
            df = df.filter(regex='^(?!Unnamed:).', axis=1)

            MODEL_SERVICIOS.write_google_sheet(df, 'servicio', my_config_constants['name_file_gsheet_servicios_dama'], session['table'])
            flash('Cruce Realizado.')
            # Actualizar fecha
            now = datetime.now()
            date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
            id = session['id']
            msj = ModelUser.update_date(db, str(id), str(date_time))
            # SQL
            # FECHA
            now = datetime.now()
            date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
            df_ppl["DATE_UPDATE"] = date_time
            df_ppl["USER"] = session['username']
            #Quitar el index
            #df_ppl = df_ppl.drop(columns=["index"])
            msj = ModelUser.upload_df(db, df_ppl, "psl_1")
            return json.dumps({'status':'OK'})
        
            
        # STEM ========================================================:
        if session['report'] == 41:
            # stem_act_1.xlsx, 'STEM_1'
            # Archivos Requeridos:
            name_load = os.path.join('stem','subidos','stem.xlsx')
            name_save = os.path.join('stem','generados', 'stem.xlsx')
            # Desde admin:
            name_pss = os.path.join('admin','admin_reportes_generales','generados','siapss.xlsx')
            name_pss2 = os.path.join('admin','admin_reportes_generales','subidos','SPP.xlsx')
            # Historico....
            #df_historico = MODEL_SERVICIOS.get_google_sheet('servicio', 'REPORTES_DAMA', 'ACMP_1')
            #df_historico = ModelUser.get_all_table(db, "acmp_1")
            df_historico = ModelUser.get_all_table(db, session["table"])
            print('HISTORICO ==================================================')
            print(len(df_historico))
            # DF:
            # src\data\stem\subidos\datos_capacitaciones_stem.xlsx
            path_capacitaciones = os.path.join('src/data', 'stem','subidos','datos_capacitaciones_stem.xlsx')
            path_manuales = os.path.join('src/data','stem','subidos','datos_manuales_stem.xlsx')
            path_formulario = os.path.join('src/data','stem','subidos','datos_form_stem.xlsx')
            
            df_capacitaciones = main_capacitaciones(path_capacitaciones)
            df_manuales = main_manuales(path_manuales)
            df_formulario = main_ETL(path_formulario)
            df_stem = concatenar_stem(df_formulario, df_manuales, df_capacitaciones)
            
            
            df_ppl, df = MODEL_SERVICIOS.make_service2pss(name_pss, name_load, name_pss2, name_save, df_historico, df_psl = df_stem)
            
            
            # NOTA: en google sheet las columnas son distintas por eso para subirlas se deberia
            # efectuar por ahora un filtrado con la variable (df)
            """
            COL_DB = ["ROL_PRINCIPAL", "DOCUMENTO", "FECHA", "SERVICIO", "MUNICIPIO", "ROL_UNIVERSIDAD",
                        "INSTITUCION", "SER_PARTE_EMPRESA", "NECESIDAD_EMPRESA", "ENCUESTA_COLEGIO",
                            "CEDULA_RI", "PERIODO", "SEDE", "FACULTAD", "COD_PLAN", "PLAN", "CONVENIO_PLAN",
                            "NIVEL", "NOMBRES", "APELLIDO1", "APELLIDO2", "T_DOCUMENTO", "EXPEDIENTE",
                                "CONVOCATORIA", "APERTURA", "ACCESO", "SUBACCESO", "MATRICULADO",
                                "CAUSA_BLOQUEO", "FECHA_BLOQUEO", "PERIODO_BLOQUEO", "EDAD", "SEXO",
                                "LOGIN", "CORREO", "ESTRATO", "PBM", "MATRICULAS", "TIPCOLEGIO", "MODACADEMICA",
                                    "ANO_TERMINACION_COLEGIO", "NODO_INICIO", "PROM_ACADEMICO_ACTUAL", "PAPA_PERIODO",
                                    "AVANCE_CARRERA", "COHORTE", "INSTITUCION_2", "MUNICIPIO_2", "PERIODO_REP"]
            """
            
            # cambiar modulo servicios de aca para abajo:
            # , my_config_constants['name_file_gsheet_servicios_dama'], session['table']
            #MODEL_SERVICIOS.write_google_sheet(df, 'servicio', 'REPORTES_DAMA', 'STEM_1')
            
            # QUEDA POR HACER COMPATIBLES LAS DOS TABLAS... PERO DE LA MANO DEL DASHBOARD 
            

            flash('Cruce Realizado.')
            # Actualizar fecha
            now = datetime.now()
            date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
            id = session['id']
            msj = ModelUser.update_date(db, str(id), str(date_time))
            # SQL
            # FECHA
            now = datetime.now()
            date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
            df_ppl["DATE_UPDATE"] = date_time
            df_ppl["USER"] = session['username']
            msj = ModelUser.upload_df(db, df_ppl, "stem_3")
            
            return json.dumps({'status':'OK'})
        
        # Autoevaluacion:
        if session['report'] == 111: 
                # Archivos Requeridos:
                # src\data\autoeval\subidos\autoeval.xlsx
                name_load = os.path.join('/home/Analisis/basic-flask-app/src/data','autoeval','subidos','autoeval.xlsx')
                name_save = os.path.join('/home/Analisis/basic-flask-app/src/data','autoeval','generados', 'autoeval.xlsx')
                
                df_historico = ModelUser.get_all_table(db, session["table"])
                #df_historico = pd.DataFrame()
                print('HISTORICO ==================================================')
                print(len(df_historico))
                # DF:
                
                # cambiar modulo servicios de aca para abajo.
                df_ppl, df_historico = main_autoeval(name_load, df_historico)
                
                # to google sheets:
                df_historico = df_historico.fillna("")
                df_ppl = df_ppl.fillna("")

                # Guardar en sheet
                # Analisar esto.....
                #MODEL_SERVICIOS.write_google_sheet(df, 'servicio', 'REPORTES_DAMA', 'ACMP_1')
                #MODEL_SERVICIOS.write_google_sheet(df_ppl, 'servicio', 'GC_def', 'Hoja 1', w=0)
                #MODEL_SERVICIOS.write_google_sheet(df_historico, 'servicio', 'GC_def', 'Hoja 2', w=0)
                
                flash('Cruce Realizado.')
                # Actualizar fecha
                now = datetime.now()
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S") # PONER HORA
                id = session['id']
                msj = ModelUser.update_date(db, str(id), str(date_time))
                # SQL
                # FECHA
                now = datetime.now()
                date_time = now.strftime("%m-%d-%Y, %H:%M:%S") # PONER HORA
                df_ppl["DATE_UPDATE"] = date_time
                df_ppl["USER"] = session['username']
                # QUITAR UNAMED
                msj = ModelUser.upload_df(db, df_ppl, session['table'])
                return json.dumps({'status':'OK'})
            


# DESCARGAR:
@app.route('/descargar/<path:filename>', methods=['POST'])
@login_required
def descargar(filename):
    try:
        path = session['path']
        uploads = os.path.join('data', path,'generados', filename)
        return send_file(uploads, as_attachment=True)
    except:
        flash("Hubo un error en encontrar los archivos.")
        return redirect(session['back_url'])

# DELETE
@app.route('/delete/<reg>/<my_user>/<date>', methods=['POST'])
def delete(reg, my_user, date):
    try:
        # Boprrar filas:
        ModelUser.delete(db, session['table'], my_user, date)
        
        # Caso Sede
        if session['report'] in [101, 102, 103]:
            # Caso SEDE:
            print("ENTRE A REPORTE:")
            google_sheet_file = my_config_constants['name_file_gsheet_sede']
            type_service = my_config_constants['type_gsheet_write_sede']
            if session["table"] == "sede_1":
                #table_to_delete_google = "MAIN"
                cols_gsh =["AVANCE_CARRERA",
                        "FACULTAD",
                        "PLAN",
                        "TIPO_NIVEL",
                        "EDAD",
                        "SEXO",
                        "DEPARTAMENTO_PROCEDENCIA",
                        "ESTRATO",
                        "PBM",
                        "MATRICULAS",
                        "PAPA",
                        "hashed_ID",
                        "NIVEL_2",
                        "DISCAPACIDAD",
                        "AVANCE_HISTOGRAMA",
                        "PERIODO_REPORTE",
                        "SUBACCESO",
                        "ID",
                        "NOMBRES",
                        "APELLIDO1",
                        "CORREO"]
            elif session["table"] == "sede_2":
                print("ENTRE A ADMINISTRATIVAS")
                #table_to_delete_google = "ADMINISTRATIVAS"
                cols_gsh = ["BLOQUEO",
                    "FACULTAD",
                    "PLAN",
                    "NIVEL",
                    "AVANCE_CARRERA",
                    "SEXO",
                    "EDAD",
                    "NUMERO_MATRICULAS",
                    "PAPA",
                    "PBM",
                    "ESTRATO",
                    "DEPTO_RESIDENCIA",
                    "DISCAPACIDAD",
                    "hashed_ID",
                    "NIVEL_2",
                    "AVANCE_HISTOGRAMA",
                    "PERIODO_REPORTE",
                    "SUBACCESO",
                    "DOCUMENTO",
                    "NOMBRES",
                    "APELLIDO1",
                    "EMAIL",
                    "ID"]
            elif session["table"] == "sede_3":
                #table_to_delete_google = "ACADEMICAS"
                cols_gsh =  [
                        "FACULTAD",
                        "PLAN",
                        "TIPO_NIVEL",
                        "SEXO",
                        "ESTRATO",
                        "DEPTO_PROCEDENCIA",
                        "NUM_MATRICULAS",
                        "PAPA",
                        "AVANCE_CARRERA",
                        "hashed_ID",
                        "NIVEL_2",
                        "DISCAPACIDAD",
                        "CAUSA_BLOQUEO",
                        "EDAD",
                        "PBM",
                        "AVANCE_HISTOGRAMA",
                        "PERIODO_REPORTE",
                        "SUBACCESO",
                        "DOCUMENTO",
                        "NOMBRES",
                        "APELLIDO1",
                        "EMAIL",
                        "ID"
                    ]
            report = 'delete_sede'
            df_historico_init = ModelUser.get_all_table(db, session["table"], report = report)
            # Verificar si el DataFrame está vacío
            if df_historico_init.empty:
                    # Especificar las columnas que quieres mantener
                    #columnas_a_mantener = ['columna1', 'columna2', 'columna3']
                    # Crear un nuevo DataFrame vacío con las columnas especificadas
                    df_historico_init  = pd.DataFrame(columns=cols_gsh)
            print("==========INFO TO ACTUALIZAR =============")
            print(df_historico_init.info())
            df_historico = df_historico_init[cols_gsh]
            print("==========INFO TO ACTUALIZAR =============")
            print(df_historico.info())
            
        else:
            type_service = 'servicio'
            google_sheet_file = my_config_constants['name_file_gsheet_servicios_dama']
            table_to_delete_google = session["table"]
            df_historico = ModelUser.get_all_table(db, session["table"]) 

            # Actualizar google sheet
        MODEL_SERVICIOS.write_google_sheet(df_historico, type_service, google_sheet_file , session["table"])
            
        return redirect(session['back_url'])
    except Exception as e:
        # Obtener el resumen del error
        print("____________________ERROR______________________________")
        print(traceback.format_exc().splitlines())
        error_message = traceback.format_exc().splitlines()[-1]
        flash(f"Hubo un error al realizar el delete: {error_message}")
        return json.dumps({'status':'OK'})
    #except:
    #    flash("Hubo un error en encontrar los archivos.")
    #    return redirect(session['back_url'])

# DOWNLOAD
@app.route('/download_upload/<reg>/<my_user>/<date>', methods=['POST'])
def down(reg, my_user, date):
    
    print("==============================$$$$$$$$$$$$$$$$$444")
    print(reg, date)
    # download_upload(self, db, table, user, date)
    df = ModelUser.download_upload(db,session['table'], my_user, date)
    print("\n \n")
    print(len(df))
    # src\data
    # src\data\my_reporte.xlsx
    path = my_config_constants["path_send_file_1"]
    df.to_excel(path , index=False)
    return send_file(path , as_attachment=True)

# Descargar tabla de actualizaciones:
@app.route('/download_upload_date', methods=['POST'])
def down_date():
    table_service = session['table']
    df_dates = ModelUser.get_distinct_V2(db,  table_service) # poner el nombre de la tabla adecuada
    # actualizar web
    MODEL_SERVICIOS.write_google_sheet(df_dates,
                                       'servicio',
                                       my_config_constants["name_file_gsheet_dates"],
                                       table_service)
    return redirect(session['back_url'])

# ============================================================================
# HTML ERROR:
# ============================================================================
def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1>Página no encontrada</h1>", 404

def status_405(error):
    return  redirect(url_for('login')), 405

# ============================================================================
# MAIN:
# ============================================================================
if __name__ == '__main__':
    #app.config.from_object(config['development'])
    #csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.register_error_handler(405, status_405)
    app.run(host='localhost', port=5000)
