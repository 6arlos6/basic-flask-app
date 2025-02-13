import os
from flask import flash
import pandas as pd
from werkzeug.utils import secure_filename
import json

#own librarys:
from src.reportes.backend.check_files import ExcelFileChecker  # Asegúrate de importar la clase correctamente
from src.reportes.backend.dll_copy import allowed_file
from src.reportes.backend.config_constants import my_config_constants

def validate_filenames(uploaded_files, session):
    """Verifica que los nombres de archivos subidos coincidan con los requeridos en la sesión."""
    if session.get('report') not in [24, 52]:
        uploaded_names = {file.filename for file in uploaded_files}
        required_files = set(session.get('required_files', []))
        return required_files.issubset(uploaded_names)
    return True


def save_files(uploaded_files, session, app):
    """Guarda los archivos subidos en la ubicación correspondiente y retorna una lista de nombres guardados."""
    filenames = []
    path = session.get('path', '')

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = determine_save_path(path, filename, session, app)
            file.save(save_path)
            filenames.append(filename)
        else:
            flash(f'El archivo {file.filename} tiene una extensión no permitida.')
    
    return filenames


def determine_save_path(path, filename, session, app):
    """Determina la ruta correcta para guardar los archivos según el reporte en la sesión."""
    base_folder = app.config['UPLOAD_FOLDER']

    if session.get('report') == 52:
        return os.path.join(base_folder, path, 'subidos', 'actividades_voluntarias', filename)
    return os.path.join(base_folder, path, 'subidos', filename)


def validate_file_structure(session, app):
    """Valida la estructura del archivo (hojas y columnas) según la configuración JSON para reportes específicos."""
    path = os.path.join(app.config['UPLOAD_FOLDER'], session.get('path', ''), 'subidos')
    # src\reportes\backend\test_structure.json
    config_path = my_config_constants["path_json_check_sede"]  # Ajusta la ruta del archivo JSON

    with open(config_path, 'r') as f:
        config = json.load(f)

    report_id = str(session.get('report'))
    checker = ExcelFileChecker(path, config, report_id)
    result = checker.run_all_checks()

    if not result['sheets_check']:
        flash(f"Hojas faltantes: {result['missing_sheets']}", 'warning')
        return False

    if not result['columns_check']:
        flash(f"Columnas faltantes: {result['missing_columns']}", 'warning')
        return False
    
    return True


def load_period(MODEL_ADMIN, session):
    """Carga y actualiza el periodo en la sesión para roles específicos."""
    try:
        path_ppl = os.path.join(my_config_constants["upload_folder"], session['path'], "subidos")
        
        if session.get('report') == 101:
            # upload_folder, sessions['path'], 'subidos'
            path_activos = os.path.join(path_ppl, "RE_MAT_PER_TABLA_DE_DATOS.xlsx")
            df = pd.read_excel(path_activos, header= 1, sheet_name= 1)
            session["periodoReporte"] = str(df["PERIODO"][0])
        elif session.get('report') == 102:
            path_activos = os.path.join( path_ppl,"BLQ_Causas_Administrativas_RE_EST_BLQ_PER_TABLA_DE_DATOS.xlsx")
            df = pd.read_excel(path_activos, header= 1, sheet_name= 1)
            session["periodoReporte"] = str(df["PERIODO_BLOQUEO"][0])
        elif session.get('report') == 103:
            path_activos = os.path.join( path_ppl,"RE_MAT_PER_TABLA_DE_DATOS.xlsx")
            df = pd.read_excel(path_activos, header= 1, sheet_name= 1)
            session["periodoReporte"] = str(df["PERIODO"][0])
        else:
            session["periodoReporte"] = "NO DEFINIDO"
    except:
        session["periodoReporte"] = "NO DEFINIDO"