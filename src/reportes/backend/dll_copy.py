import pandas as pd
import os
from src.reportes.security.update_google_sheet import my_worksheet
from flask import Flask, render_template
from unidecode import unidecode
import json
# get close matches
from difflib import get_close_matches
from datetime import datetime
import re

class ExcelPreprocessMain:
  def __init__(self, path_gen):
    self.path = path_gen
  # LOAD:
  def load(self, name, sheet_name, header):
    io = os.path.join(self.path,name)
    df = pd.read_excel(io, sheet_name = sheet_name, header = header)
    return df
  # WRITES:
  def write(self, df, name, ind=False):
    io = os.path.join(self.path, name)
    df.to_excel(io,index=ind)
  # WRITES ENGINE:
  def write_engine(self, list_dfs, name, ind=False):
    io = os.path.join(self.path, name)
    writer = pd.ExcelWriter(io, engine='xlsxwriter')
    for tpl_df in list_dfs:
      df, name = tpl_df
      df.to_excel(writer, sheet_name = name, index=ind)
    writer.close()
  # WRITES GOOGLE SHEET:
  def write_google_sheet(self, df, rol, documento, hoja, w=0):
    if w == 0:
      work_s = my_worksheet(rol, documento, hoja)
      work_s.clear()
      work_s.update([df.columns.values.tolist()] + df.values.tolist(), value_input_option='USER_ENTERED')
    else:
      filas = len(df)
      columnas = len(df.columns)
      work_s = my_worksheet(rol, documento, hoja, row = filas, col = columnas)
      work_s.clear()
      work_s.update([df.columns.values.tolist()] + df.values.tolist(), value_input_option='USER_ENTERED')
  def get_google_sheet(self,rol,documento,hoja):
    work_s = my_worksheet(rol, documento, hoja)
    df = pd.DataFrame(work_s.get_all_records(numericise_ignore=['all']))
    return df
  
class ExcelServicios(ExcelPreprocessMain):
  def make_service2pss(self, name_pss, name_load, name_pss2, name_save, df_historico, df_psl = None):
    # Cargar siapss:
    df_siaspp = self.load(name_pss, 0, 0)
    # Cargar unal_lee subido principal (excepcional con el caso de PSL act voluntarias):
    if df_psl is None:
      df_ppl = self.load(name_load, 0, 0)
    else:
      df_ppl = df_psl.copy()
      print("ENTRADA EN MAKE SERVICE ================")
      print(df_ppl.info())
    # Convert fecha a datetime y errores volver NaT:
    df_ppl['FECHA'] = pd.to_datetime(df_ppl['FECHA'], errors='coerce')
    # Rellenar datos perdidos en fecha (para arriba, para abajo):
    df_ppl[['FECHA']] = df_ppl[['FECHA']].fillna(method='ffill')
    df_ppl[['FECHA']] = df_ppl[['FECHA']].fillna(method='bfill')
    # ============== hacer lo mismo de fecha pero para historico:
    # Nota: El historico viene VARCHAR -> hacer esto es importante
    # y esta bien.
    try:
      # Convert fecha a datetime y errores volver NaT:
      df_historico['FECHA'] = pd.to_datetime(df_historico['FECHA'], errors='coerce')
      # Rellenar datos perdidos en fecha (para arriba, para abajo):
      df_historico[['FECHA']] = df_historico[['FECHA']].fillna(method='ffill')
      df_historico[['FECHA']] = df_historico[['FECHA']].fillna(method='bfill')
    except:
      pass
    # Convertir documento a texto:
    df_ppl['DOCUMENTO'] = df_ppl['DOCUMENTO'].fillna('').astype(str).str.replace(".0","",regex=False)
    # ====================================================
    # Encuentro los programas parecidos con los nombres oficiales:
    df_ppl['PROGRAMA'] = df_ppl['PROGRAMA'].str.upper()
    df_ppl['PROGRAMA'] = df_ppl['PROGRAMA'].apply(encontrar_mas_cercano, case_match = 2)
    # Quitar informacion redudante con el SIA:
    df_ppl_2 = df_ppl.drop(columns=['NOMBRES Y APELLIDOS','PROGRAMA','CORREO'])
    # Juntar df actual con siaspp:
    df_ppl_3 = pd.merge(df_ppl_2, df_siaspp, how = 'left', on='DOCUMENTO')
    # Copia del df merged:
    df_ppl_3_copy = df_ppl_3.copy()
    # De PLAN == NULL en SIA tomar indices y remplazar por los "PROGRAMA"
    # previamente "matcheados"
    index_nan_PLAN = df_ppl_3_copy[df_ppl_3['PLAN'].isnull()].index
    df_ppl_3_copy.loc[index_nan_PLAN ,'PLAN'] = df_ppl['PROGRAMA']
    # Si la hoja de datos tiene la columna "MI-FACULTAD"...
    if 'MI-FACULTAD' in list(df_ppl_3_copy.columns):
      # Idenfificar indices de FACULDAD (SIA) nulos y "":
      index_nan_FACULTAD = df_ppl_3_copy[ (df_ppl_3['FACULTAD'].isnull()) | (df_ppl_3['FACULTAD'] == '')].index
      # Preparar "MI-FACULTAD" poniendolo en UPPER y encontrandole matches oficiales:
      df_ppl_3_copy['MI-FACULTAD'] = df_ppl_3_copy['MI-FACULTAD'].str.upper()
      df_ppl_3_copy['MI-FACULTAD'] = df_ppl_3_copy['MI-FACULTAD'].apply(encontrar_mas_cercano, case_match = 1)
      # En los index NaN o "" de FACULTAD poner los correspondientes "MI-FACULTAD"
      df_ppl_3_copy.loc[index_nan_FACULTAD ,'FACULTAD'] = df_ppl_3_copy['MI-FACULTAD']
      # Volver a hacer el proceso pero esta vez con los datos de facultad no matcheados:
      # rellenar con los valores de PROGRAMA:
      index_nan_FACULTAD = df_ppl_3_copy[df_ppl_3_copy['FACULTAD'].isnull() | (df_ppl_3_copy['FACULTAD'] == '')].index
      values_PLAN = df_ppl_3_copy.loc[index_nan_FACULTAD, 'PLAN']
      # Tomar todos los valores df_ppl_3_copy y añadir "FAC"
      merged_data = df_ppl_3_copy.merge(df_nueva, left_on='PLAN', right_on='NOMID1', how='left')
      # De merged_data con los indices nan o "" tomar 'FAC'
      values_A = merged_data.loc[index_nan_FACULTAD, 'FAC']
      # Reemplazarlo en su ubicacion correspondiente:
      df_ppl_3_copy.loc[index_nan_FACULTAD, 'FACULTAD'] = values_A
    else:
      # Hacer lo mismo que se hizo anteriormente pero sin el proceso de "MI-FACULTAD"
      index_nan_FACULTAD = df_ppl_3_copy[df_ppl_3['FACULTAD'].isnull() | (df_ppl_3['FACULTAD'] == '')].index
      values_PLAN = df_ppl_3_copy.loc[index_nan_FACULTAD, 'PLAN']
      # df_nueva = df_planes[['FACULTAD', 'NOMID1']].copy()
      merged_data = df_ppl_3_copy.merge(df_nueva, left_on='PLAN', right_on='NOMID1', how='left')
      values_A = merged_data.loc[index_nan_FACULTAD, 'FAC']
      df_ppl_3_copy.loc[index_nan_FACULTAD, 'FACULTAD'] = values_A
    # volver a cargar DPSS
    df_pss2 = self.load(name_pss2, 0, 0) # cargo programa de gov.
    # Convertir documento a texto:
    df_pss2['DOCUMENTO'] = df_pss2['DOCUMENTO'].fillna('').astype(str).str.replace(".0","",regex=False)
    # Obtengo documento de filas donde cohorte es nulo:
    df_ppl_5 = df_ppl_3[df_ppl_3['COHORTE'].isnull()]['DOCUMENTO']
    # Busco todas las filas de df_pss2 donde cohorte es nulo:
    df_pss2_R = df_pss2.loc[df_pss2['DOCUMENTO'].isin(list(df_ppl_5))]
    # Tomo cedulas de filas nulas:
    Ced_gov_null = list(df_pss2_R['DOCUMENTO'])
    # Por cada una pongo en COHORTE el valor de dpss
    for cc in Ced_gov_null:
      df_ppl_3_copy.loc[df_ppl_3_copy.DOCUMENTO == cc, 'COHORTE'] = list(df_pss2_R[df_pss2_R.DOCUMENTO == cc]['COHORTE'])[0]
    # En los que definitivamente no se encontro, se busca y se pone Estudiante Regular:
    index_nan_CO = df_ppl_3_copy[ df_ppl_3_copy['COHORTE'].isnull() ].index
    df_ppl_3_copy.loc[index_nan_CO ,'COHORTE'] = 'Estudiante Regular'
    # Convertir a texto Cedula-Ri:
    df_ppl_3_copy['CEDULA-RI'] = df_ppl_3_copy['CEDULA-RI'].fillna('').astype(str).str.replace(".0","",regex=False)
    # Rellenar todos los valores con valores vacios:
    df_ppl_3_copy = df_ppl_3_copy.fillna(value='')
    # Quitar tildes y espacios:
    columnas = list(df_ppl_3_copy.columns)
    for col in columnas:
      if col not in ['PROM_ACADEMICO_ACTUAL','PAPA_PERIODO','AVANCE_CARRERA']:
        try:
          df_ppl_3_copy[col] = df_ppl_3_copy[col].apply(unidecode)
          df_ppl_3_copy[col] = df_ppl_3_copy[col].str.strip()
        except:
          pass
      # ============ MODIFICACION PARA PASAR TODA LA COL
      else:
        try:
          df_ppl_3_copy[col] = df_ppl_3_copy[col].astype(str)
          df_ppl_3_copy[col] = df_ppl_3_copy[col].str.replace(".",",")
        except:
          pass
    try:
      df_historico.FECHA = pd.to_datetime(df_historico.FECHA, format='%d/%m/%Y')
    except:
      pass
    # Concatenar historico con actual:

    #==================== NUEVO PARA SOPESAR QUE CUANDO SI HAY HISTORICO
    # =================== PUEDE QUE HAYAN NOMBRES DE COLS REPETIDAS:
    cols = df_ppl_3_copy.columns
    cols_tupl = [col.replace('-','_') for col in cols]
    cols_tupl = [col.replace(' ','_') for col in cols_tupl]
    cols_tupl = [unidecode(col) for col in cols_tupl]
    df_ppl_3_copy.columns = cols_tupl

    # =============================================================

    df_concat = pd.concat([df_historico, df_ppl_3_copy])
    # Ordenar la df en funcion de la fecha:
    df_ppl_3_copy.sort_values(by='FECHA', inplace = True)
    df_concat.sort_values(by='FECHA', inplace = True)
    # Convertirla a string:
    df_concat['FECHA'] = df_concat['FECHA'].dt.strftime("%d/%m/%Y")
    # Rellenar todos los valores con valores vacios:
    df_concat = df_concat.fillna('')
    # Capitalizar todo el texto:
    for col in df_ppl_3_copy.columns:
      if df_ppl_3_copy[col].dtype == 'object':  # Verificar si la columna contiene texto
          df_ppl_3_copy[col] = df_ppl_3_copy[col].apply(capitalize_text)
    for col in df_concat.columns:
      if df_concat[col].dtype == 'object':  # Verificar si la columna contiene texto
          df_concat[col] = df_concat[col].apply(capitalize_text)
    # Quitar unameds:
    # Identificar todas las columnas que empiezan con 'Unnamed:'
    
    columns_to_drop = [col for col in df_ppl_3_copy.columns if col.startswith('Unnamed:')]
    # Eliminar dichas columnas del DataFrame
    df_ppl_3_copy.drop(columns=columns_to_drop, inplace=True)
    
    columns_to_drop = [col for col in df_concat.columns if col.startswith('Unnamed:')]
    # Eliminar dichas columnas del DataFrame
    df_concat.drop(columns=columns_to_drop, inplace=True)
    
    # Escribo documento excel:
    list_dfs = [
            (df_ppl_3_copy, 'PRINCIPAL'),
            (df_concat, 'HISTORICO')
              ]
    self.write_engine(list_dfs, name_save)
    # Devuelvo info actual + historica:
    # ::::::::::::::::::::::::::::
    df_ppl_3_copy = fill_empty_spaces(df_ppl_3_copy)
    df_concat = fill_empty_spaces(df_concat)  
    print("====== ANTES DE ESCRIBIR ===================")
    try:
       df_concat["PERIODO_AT"] = df_concat["PERIODO_AT"].astype(str)
    except:
       pass
    print(df_concat.info())                          
    return df_ppl_3_copy, df_concat


  def make_serviceUTP(self, name_pss, name_load, name_pss2, name_save, df_historico):
    # Cargar siapss:
    #df_siaspp = self.load(name_pss, 0, 0)
    # Cargar unal_lee subido principal:
    df_ppl = self.load(name_load, 0, 0)
    # Convert fecha a datetime y errores volver NaT:
    df_ppl['FECHA'] = pd.to_datetime(df_ppl['FECHA'], errors='coerce')
    # Rellenar datos perdidos en fecha (para arriba, para abajo):
    df_ppl[['FECHA']] = df_ppl[['FECHA']].fillna(method='ffill')
    df_ppl[['FECHA']] = df_ppl[['FECHA']].fillna(method='bfill')
    # ============== hacer lo mismo de fecha pero para historico:
    # Nota: El historico viene VARCHAR -> hacer esto es importante
    # y esta bien.
    try:
      # Convert fecha a datetime y errores volver NaT:
      df_historico['FECHA'] = pd.to_datetime(df_historico['FECHA'], errors='coerce')
      # Rellenar datos perdidos en fecha (para arriba, para abajo):
      df_historico[['FECHA']] = df_historico[['FECHA']].fillna(method='ffill')
      df_historico[['FECHA']] = df_historico[['FECHA']].fillna(method='bfill')
    except:
      pass
    # Convertir documento a texto:
    #df_ppl['DOCUMENTO'] = df_ppl['DOCUMENTO'].fillna('').astype(str).str.replace(".0","",regex=False)
    # ====================================================
    # Encuentro los programas parecidos con los nombres oficiales:
    df_ppl['PROGRAMA DEPARTAMENTO'] = df_ppl['PROGRAMA DEPARTAMENTO'].str.upper()
    df_ppl['PROGRAMA DEPARTAMENTO'] = df_ppl['PROGRAMA DEPARTAMENTO'].apply(encontrar_mas_cercano, case_match = 2)
    # Quitar informacion redudante con el SIA:
    #df_ppl_2 = df_ppl.drop(columns=['NOMBRES Y APELLIDOS','PROGRAMA','CORREO'])
    # Juntar df actual con siaspp:
    #df_ppl_3 = pd.merge(df_ppl_2, df_siaspp, how = 'left', on='DOCUMENTO')
    # Copia del df merged:
    #df_ppl_3_copy = df_ppl_3.copy()
    # De PLAN == NULL en SIA tomar indices y remplazar por los "PROGRAMA"
    # previamente "matcheados"
    #index_nan_PLAN = df_ppl_3_copy[df_ppl_3['PLAN'].isnull()].index
    #df_ppl_3_copy.loc[index_nan_PLAN ,'PLAN'] = df_ppl['PROGRAMA']
    # Si la hoja de datos tiene la columna "MI-FACULTAD"...
    #if 'MI-FACULTAD' in list(df_ppl_3_copy.columns):
      # Idenfificar indices de FACULDAD (SIA) nulos y "":
    #  index_nan_FACULTAD = df_ppl_3_copy[ (df_ppl_3['FACULTAD'].isnull()) | (df_ppl_3['FACULTAD'] == '')].index
      # Preparar "MI-FACULTAD" poniendolo en UPPER y encontrandole matches oficiales:
    #  df_ppl_3_copy['MI-FACULTAD'] = df_ppl_3_copy['MI-FACULTAD'].str.upper()
    #  df_ppl_3_copy['MI-FACULTAD'] = df_ppl_3_copy['MI-FACULTAD'].apply(encontrar_mas_cercano, case_match = 1)
      # En los index NaN o "" de FACULTAD poner los correspondientes "MI-FACULTAD"
    #  df_ppl_3_copy.loc[index_nan_FACULTAD ,'FACULTAD'] = df_ppl_3_copy['MI-FACULTAD']
      # Volver a hacer el proceso pero esta vez con los datos de facultad no matcheados:
      # rellenar con los valores de PROGRAMA:
    #  index_nan_FACULTAD = df_ppl_3_copy[df_ppl_3_copy['FACULTAD'].isnull() | (df_ppl_3_copy['FACULTAD'] == '')].index
    #  values_PLAN = df_ppl_3_copy.loc[index_nan_FACULTAD, 'PLAN']
      # Tomar todos los valores df_ppl_3_copy y añadir "FAC"
    #  merged_data = df_ppl_3_copy.merge(df_nueva, left_on='PLAN', right_on='NOMID1', how='left')
      # De merged_data con los indices nan o "" tomar 'FAC'
    #  values_A = merged_data.loc[index_nan_FACULTAD, 'FAC']
      # Reemplazarlo en su ubicacion correspondiente:
    # df_ppl_3_copy.loc[index_nan_FACULTAD, 'FACULTAD'] = values_A
    #else:
      # Hacer lo mismo que se hizo anteriormente pero sin el proceso de "MI-FACULTAD"
    #  index_nan_FACULTAD = df_ppl_3_copy[df_ppl_3['FACULTAD'].isnull() | (df_ppl_3['FACULTAD'] == '')].index
    #  values_PLAN = df_ppl_3_copy.loc[index_nan_FACULTAD, 'PLAN']
      # df_nueva = df_planes[['FACULTAD', 'NOMID1']].copy()
    #  merged_data = df_ppl_3_copy.merge(df_nueva, left_on='PLAN', right_on='NOMID1', how='left')
    #  values_A = merged_data.loc[index_nan_FACULTAD, 'FAC']
    #  df_ppl_3_copy.loc[index_nan_FACULTAD, 'FACULTAD'] = values_A
    # volver a cargar DPSS
    #df_pss2 = self.load(name_pss2, 0, 0) # cargo programa de gov.
    # Convertir documento a texto:
    #df_pss2['DOCUMENTO'] = df_pss2['DOCUMENTO'].fillna('').astype(str).str.replace(".0","",regex=False)
    # Obtengo documento de filas donde cohorte es nulo:
    #df_ppl_5 = df_ppl_3[df_ppl_3['COHORTE'].isnull()]['DOCUMENTO']
    # Busco todas las filas de df_pss2 donde cohorte es nulo:
    #df_pss2_R = df_pss2.loc[df_pss2['DOCUMENTO'].isin(list(df_ppl_5))]
    # Tomo cedulas de filas nulas:
    #Ced_gov_null = list(df_pss2_R['DOCUMENTO'])
    # Por cada una pongo en COHORTE el valor de dpss
    #for cc in Ced_gov_null:
    #  df_ppl_3_copy.loc[df_ppl_3_copy.DOCUMENTO == cc, 'COHORTE'] = list(df_pss2_R[df_pss2_R.DOCUMENTO == cc]['COHORTE'])[0]
    # En los que definitivamente no se encontro, se busca y se pone Estudiante Regular:
    #index_nan_CO = df_ppl_3_copy[ df_ppl_3_copy['COHORTE'].isnull() ].index
    #df_ppl_3_copy.loc[index_nan_CO ,'COHORTE'] = 'Estudiante Regular'
    # Convertir a texto Cedula-Ri:
    #df_ppl_3_copy['CEDULA-RI'] = df_ppl_3_copy['CEDULA-RI'].fillna('').astype(str).str.replace(".0","",regex=False)
    # Rellenar todos los valores con valores vacios:
    #df_ppl_3_copy = df_ppl_3_copy.fillna(value='')
    # Quitar tildes y espacios:
    #columnas = list(df_ppl_3_copy.columns)
    #for col in columnas:
    #  if col not in ['PROM_ACADEMICO_ACTUAL','PAPA_PERIODO','AVANCE_CARRERA']:
    #    try:
    #      df_ppl_3_copy[col] = df_ppl_3_copy[col].apply(unidecode)
    #      df_ppl_3_copy[col] = df_ppl_3_copy[col].str.strip()
    #    except:
    #      pass
      # ============ MODIFICACION PARA PASAR TODA LA COL
    #  else:
    #    try:
    #      df_ppl_3_copy[col] = df_ppl_3_copy[col].astype(str)
    #      df_ppl_3_copy[col] = df_ppl_3_copy[col].str.replace(".",",")
    #    except:
    #      pass
    try:
      df_historico.FECHA = pd.to_datetime(df_historico.FECHA, format='%d/%m/%Y')
    except:
      pass
    # Concatenar historico con actual:

    #==================== NUEVO PARA SOPESAR QUE CUANDO SI HAY HISTORICO
    # =================== PUEDE QUE HAYAN NOMBRES DE COLS REPETIDAS:
    cols = df_ppl.columns
    cols_tupl = [col.strip() for col in cols]
    cols_tupl = [col.replace('-','_') for col in cols_tupl]
    cols_tupl = [col.replace(' ','_') for col in cols_tupl]
    cols_tupl = [unidecode(col) for col in cols_tupl]
    df_ppl.columns = cols_tupl

    # =============================================================

    df_concat = pd.concat([df_historico, df_ppl])
    # Ordenar la df en funcion de la fecha:
    df_ppl.sort_values(by='FECHA', inplace = True)
    df_concat.sort_values(by='FECHA', inplace = True)
    # Convertirla a string:
    df_concat['FECHA'] = df_concat['FECHA'].dt.strftime("%d/%m/%Y")
    # Rellenar todos los valores con valores vacios:
    df_concat = df_concat.fillna('')
    # Poner capitalice
    for col in df_concat.columns:
      if df_concat[col].dtype == 'object':  # Verificar si la columna contiene texto
          df_concat[col] = df_concat[col].apply(capitalize_text)
    for col in df_ppl.columns:
      if df_ppl[col].dtype == 'object':  # Verificar si la columna contiene texto
          df_ppl[col] = df_ppl[col].apply(capitalize_text)
    # Escribo documento excel:
    list_dfs = [
            (df_ppl, 'PRINCIPAL'),
            (df_concat, 'HISTORICO')
              ]
    self.write_engine(list_dfs, name_save)
    # Devuelvo info actual + historica:
    return df_ppl, df_concat
class ExcelAdmin2(ExcelPreprocessMain):
  def main_siaspp2(self,name_pss, name_estudiantes_ant, name_estudiantes_now, name_lists, name_save, periodo='2022-2S'):
    df_pss = self.load(name_pss, 0, 0) # CARGAR PILOS
    df_mib_ant = self.load(name_estudiantes_ant, 1, 1) # CARGAR SIA ANTERIOR
    df_mib_now = self.load(name_estudiantes_now, 1, 1) # CARGAR SIA HOY
    df_hoy_ant = pd.concat([df_mib_now, df_mib_ant]) # Concatenar sia hoy con anterior
    result_df = df_hoy_ant.drop_duplicates(subset=['DOCUMENTO'], keep='first')

    # Desde aquí...
    col_main = list(result_df.columns) # columnas requeridas
    for name in name_lists:
      df_asig = self.load(name , 1, 1) # cargar df asignaturas (este es general)
      col_asig = list(df_asig.columns) # columnas nuevas
      z = set(col_main).intersection(set(col_asig)) # cols de interseccion
      drop_cols = set(col_asig) - z # quitar las col no interseccion
      df_asing_new = df_asig.drop(columns=list(drop_cols)) # Borrar todas las no inters
      df_asing_new = df_asing_new.fillna('') # rellenar nans
      df_asing_new = df_asing_new.drop_duplicates(subset=['DOCUMENTO']) # borrar duplicados by documento
      set_doc_main = set(result_df.DOCUMENTO)
      set_doc_sec = set(df_asing_new.DOCUMENTO)
      z_doc = set_doc_sec - set_doc_main # set de cols que no estan 
      print(len(z_doc))
      # Tomar todas las filas que se encuentran en la lista de las cedulas que no estan en el df
      # principal y crear una nueva dataframe
      df_asing_new_rest = df_asing_new.loc[df_asing_new['DOCUMENTO'].isin(list(z_doc))]
      # Poner PERIODO
      if 'PERIODO' not in df_asing_new_rest.columns:
        df_asing_new_rest.PERIODO = periodo
      result_df = pd.concat([result_df, df_asing_new_rest])
    # Continuar con el proceso ....
    df_drop_correo = df_pss.drop(columns=['CORREO'])
    df_drop_correo.DOCUMENTO = df_drop_correo.DOCUMENTO.astype('str')
    df_siaspp = pd.merge(result_df, df_drop_correo, how = 'left', on='DOCUMENTO')
    df_siaspp['COHORTE'] =  df_siaspp['COHORTE'].fillna('Estudiante Regular')
    self.write(df_siaspp, name_save)
    df_siaspp=  df_siaspp.fillna('')
    return df_siaspp

'''
class ExcelFacultades(ExcelPreprocessMain):
  def main_facultad(self, name_act, name_nod, name_est, name_save, facultad, periodo):
    df_act = self.load(name_act, 1, 1)
    df_nod = self.load(name_nod, 1, 1)
    df_est = self.load(name_est, 1, 1)
    # col seleccionadas df_act:
    col_act = [
        'FACULTAD',
        'COD_PLAN', 'PLAN',
        'CONVENIO_PLAN',
        'COD_NIVEL', 'NIVEL', 'HIST_ACAD', 'AVANCE_CARRERA', 'DOCUMENTO',
        'NOMBRES', 'APELLIDO1', 'APELLIDO2', 'NOMBRES_APELLIDOS', 'COD_ACCESO',
        'ACCESO', 'COD_SUBACCESO', 'SUBACCESO', 'CONVOCATORIA', 'APERTURA',
        'T_DOCUMENTO', 'GENERO', 'EMAIL', 'USUARIO', 'CODIGO',
        'FECHA_NACIMIENTO', 'EDAD', 'NUMERO_MATRICULAS', 'PAPA', 'PROME_ACADE',
        'PBM_CALCULADO', 'ESTRATO','DEPTO_RESIDENCIA','MUNICIPIO_RESIDENCIA', 'PAIS-NACIONALIDAD',
        'VICTIMAS_DEL_CONFLICTO', 'DISCAPACIDAD','COD_NODO_INICIO', 'NODO_INICIO','ESTADO', 'CARACTER_COLEGIO'
    ]
    df_act = df_act[col_act]
    # col seleccionadas df_nod:
    col_nod = [
        'COD_PROG_CURRICULAR', 'PROG_CURRICULAR',
          'COD_FACULTAD', 'FACULTAD', 'TIPO_NIVEL', 'COD_PLAN', 'PLAN', 'NOMBRES',
          'APELLIDO1', 'APELLIDO2', 'DOCUMENTO', 'HIST_ACADEMICA', 'EMAIL',
          'CONVOCATORIA', 'APERTURA', 'PERIODO_FINALIZACION',
          'COD_NODO_FINALIZACION', 'NODO_FINALIZACION', 'PERIODO_GRADUACION',
          'COD_NODO_GRADUACION', 'NODO_GRADUACION', 'FECHA_GRADO', 'TITULO','PROM_GRADUADO'
    ]
    df_nod = df_nod[col_nod]
    # col seleccionadas df_nod:
    col_est = [
        'PERIODO', 'FACULTAD', 'TIPO_NIVEL',
        'COD_PLAN', 'PLAN', 
        'DOCUMENTO', 'NOMBRES', 'APELLIDOS',
        'CORREO', 'CONVOCATORIA', 'APERTURA', 'COD_ASIGNATURA', 'ASIGNATURA',
        'TIPOLOGIA', 'CREDITOS_ASIGNATURA',
        'UAB_ASIGNATURA',
        'CALIFICACION_ALFABETICA', 'CALIFICACION_NUMERICA', 'TIPO',
        'VECES_VISTA'
    ]
    df_est = df_est[col_est]

    df_act = normalizacion_col("FACULTAD", df_act)
    df_nod = normalizacion_col("FACULTAD", df_nod)
    df_est = normalizacion_col("FACULTAD", df_est)

    df_act_fac = df_act[df_act.FACULTAD == facultad]
    df_nod_fac = df_nod[df_nod.FACULTAD == facultad]
    df_est_fac = df_est[df_est.FACULTAD == facultad]

    

    try:
        # nod -> FECHA_GRADO
        # act -> FECHA_NACIMIENTO
        df_act_fac['FECHA_NACIMIENTO'] = df_act_fac['FECHA_NACIMIENTO'].dt.strftime("%d/%m/%Y")
        df_nod_fac['FECHA_GRADO'] = df_nod_fac['FECHA_GRADO'].dt.strftime("%d/%m/%Y")
    except:
      pass
    
    df_act_fac = df_act_fac.fillna('')
    df_nod_fac = df_nod_fac.fillna('')
    df_est_fac = df_est_fac.fillna('')

    # periodo reporte:
    df_act_fac["PERIODO_REPORTE"] = periodo
    df_nod_fac ["PERIODO_REPORTE"] = periodo
    df_est_fac["PERIODO_REPORTE"] = periodo

    # Escribo documento excel:
    list_dfs = [
            (df_act_fac, 'ACT'),
            (df_nod_fac, 'NOD'),
            (df_est_fac, 'EST')
              ]
    self.write_engine(list_dfs, name_save)
    return df_act_fac, df_nod_fac, df_est_fac
'''


class ExcelFacultades(ExcelPreprocessMain):
  def main_facultad(self, name_act, name_nod, name_est, name_save, facultad, periodo):
    df_act = self.load(name_act, 1, 1)
    # col seleccionadas df_act:
    col_act = [
        'FACULTAD',
        'COD_PLAN', 'PLAN',
        'CONVENIO_PLAN',
        'COD_NIVEL', 'NIVEL', 'HIST_ACAD', 'AVANCE_CARRERA', 'DOCUMENTO',
        'NOMBRES', 'APELLIDO1', 'APELLIDO2', 'NOMBRES_APELLIDOS', 'COD_ACCESO',
        'ACCESO', 'COD_SUBACCESO', 'SUBACCESO', 'CONVOCATORIA', 'APERTURA',
        'T_DOCUMENTO', 'GENERO', 'EMAIL', 'USUARIO', 'CODIGO',
        'FECHA_NACIMIENTO', 'EDAD', 'NUMERO_MATRICULAS', 'PAPA', 'PROME_ACADE',
        'PBM_CALCULADO', 'ESTRATO','DEPTO_RESIDENCIA','MUNICIPIO_RESIDENCIA', 'PAIS-NACIONALIDAD',
        'VICTIMAS_DEL_CONFLICTO', 'DISCAPACIDAD','COD_NODO_INICIO', 'NODO_INICIO','ESTADO', 'CARACTER_COLEGIO'
    ]
    df_act = df_act[col_act]
    df_act = normalizacion_col("FACULTAD", df_act)
    df_act_fac = df_act[df_act.FACULTAD == facultad]
    try:
        # nod -> FECHA_GRADO
        # act -> FECHA_NACIMIENTO
        df_act_fac['FECHA_NACIMIENTO'] = df_act_fac['FECHA_NACIMIENTO'].dt.strftime("%d/%m/%Y")
    except:
      pass
    df_act_fac = df_act_fac.fillna('')
    # periodo reporte:
    df_act_fac["PERIODO_REPORTE"] = periodo
    # Escribo documento excel:
    list_dfs = [
            (df_act_fac, 'ACT')
              ]
    self.write_engine(list_dfs, name_save)

    # dummy:
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()
    return df_act_fac, df1, df2



class ExcelSia(ExcelPreprocessMain):
  def main_matriculados(self,name_asignaturas,name_estudiantes_now,name_estudiantes_ant,name_matr_ib, name_matr_pp, name_save, periodo, df_historico):
    PATH_PRINCIPAL = self.path
    # Asignarutas inscritas:
    path_1 = os.path.join(PATH_PRINCIPAL,name_asignaturas)
    df_asignaturas_inscritas = pd.read_excel(path_1, sheet_name=1, header=1)
    # Filtrar cedulas distintas por inscritos:
    set_docs = set(df_asignaturas_inscritas['DOCUMENTO'].to_list())
    #set_docs = list(set_docs)[:nn] # SOLO HASTA 50
    # Cargar Informacion básica 2022 - 2s:
    path_2 = os.path.join(PATH_PRINCIPAL, name_estudiantes_now)
    df_mib_now = pd.read_excel(path_2,sheet_name=1,header=1)
    # Cargar Informacion básica 2022-1s:
    path_3 = os.path.join(PATH_PRINCIPAL, name_estudiantes_ant)
    df_mib_ant = pd.read_excel(path_3,sheet_name=1,header=1)
    # Cargar Matriculados Info Básica:
    path_4 = os.path.join(PATH_PRINCIPAL, name_matr_ib)
    df_MIB = pd.read_excel(path_4,sheet_name=1,header=1)
    # Cargar Matriculados por periodo:
    path_5 = os.path.join(PATH_PRINCIPAL, name_matr_pp)
    df_MPP = pd.read_excel(path_5, sheet_name=1, header=1)
    print("======================================")
    print('TODAS LAS BASES DE DATOS CARGADAS. :) ')
    print("======================================")
    # CRUCE:
    # Listas vacias por caracteristica:
    Creditos_inscritos = []
    Genero = []
    Depart_nacimiento = []
    Cedula = []
    Cod_plan = []
    Plan = []
    Avance = []
    Tipo_de_Nivel = []
    Convocatoria = []
    Apertura = []
    # CRUCE:
    for ind, dni in enumerate(set_docs):
      # INSCRITOS:
      creditos_totales = DNI_2_TotCred(dni, df_asignaturas_inscritas)
      # COD_PLAN
      cod_plan = DNI_2_Feature(dni, 'COD_PLAN', df_asignaturas_inscritas)
      # PLAN
      plan = DNI_2_Feature(dni, 'PLAN', df_asignaturas_inscritas)
      # TIPO DE NIVEL TIPO_NIVEL
      tipo_nivel = DNI_2_Feature(dni, 'TIPO_NIVEL', df_asignaturas_inscritas)
      # CONVOCATORIA:
      convocatoria = DNI_2_Feature(dni, 'CONVOCATORIA', df_asignaturas_inscritas)
      # APERTURA:
      apertura = DNI_2_Feature(dni, 'APERTURA', df_asignaturas_inscritas)
      # SEXO:
      sexo = DNI_2_Feature(dni, 'SEXO', df_mib_ant) # 'M', 'F', 'INDEFINIDO'
      if sexo == 'INDEFINIDO':
        sexo = DNI_2_Feature(dni, 'SEXO', df_mib_now) # 'M', 'F', 'INDEFINIDO'
      # DEPARTAMENTO:
      departamento = DNI_2_Feature(dni, 'DEPARTAMENTO_PROCEDENCIA', df_MPP) # DEP o INDEFINIDO
      # AVANCE_CARRERA
      # df_basicos 
      # df_MPP
      # df_matriculados
      prc = DNI_2_Feature(dni, 'AVANCE_CARRERA', df_mib_now)
      if prc == -5:
        prc = DNI_2_Feature(dni, 'AVANCE_CARRERA', df_mib_ant)
        if prc == -5:
          prc = DNI_2_Feature(dni, 'AVANCE_CARRERA',df_MIB)
      # AGREGAR:
      Cedula.append(dni)
      Creditos_inscritos.append(creditos_totales)
      Genero.append(sexo)
      Depart_nacimiento.append(departamento)
      Cod_plan.append(cod_plan)
      Plan.append(plan)
      Avance.append(prc)
      Tipo_de_Nivel.append(tipo_nivel)
      Convocatoria.append(convocatoria)
      Apertura.append(apertura)
    print("======================================")
    print('CRUCE REALIZADO! :) ')
    print("======================================")
    # Crear dataframe final:
    df1 = pd.DataFrame({
        'CEDULA': Cedula,
        'SEXO': Genero,
        'TOTAL_CREDITOS': Creditos_inscritos,
        'DEPARTAMENTO':Depart_nacimiento,
        'COD_PLAN':Cod_plan,
        'PLAN':Plan,
        'AVANCE':Avance,
        'NIVEL_ESTUDIOS':Tipo_de_Nivel,
        'CONVOCATORIA':Convocatoria,
        'APERTURA':Apertura
    })
    # Borrar NAN en df1
    df1['PERIODO_REPORTE'] = periodo

    df_concat = pd.concat([df_historico, df1])
    df_concat = df_concat.fillna('')
    list_dfs = [
            (df1, 'PRINCIPAL'),
            (df_concat, 'HISTORICO')
              ]
    self.write_engine(list_dfs, name_save)
    return df_concat
  
  def estadisticas_1(self, name_sia_grphor):
    # cargar horarios y grupos:
    df_hr_gr = self.load(name_sia_grphor, 1, 0)
    ubgga_ass = df_hr_gr['UBGAA_ASS']
    # Campos:
    departamento = []
    asignaturas = []
    grupos = [] 
    cupos = []
    inscritos = []
    # Departamentos:
    Departamentos = set(ubgga_ass.to_list())

    for dep in Departamentos:
      # por cada departamento tomar un trozo de datos:
      df = df_hr_gr[df_hr_gr['UBGAA_ASS'] == dep]
      # tomar nombre se asignatura, id grupo, cupo y numero de inscritos:
      df_asignaturas = df['NOMBRE_ASS']
      # (Correccion: hacer set teniendo en cuenta la asignatura, porque los grupos pueden ser llamados igual)
      n_asg = len(set(df_asignaturas)) # Numero de asignaturas distintas.
      # Numero de grupos distintos
      grup = df['NOMBRE_ASS'] + '-' + df['PPAL_ID_GRUPO_ACTIVIDAD']
      df_grupos = set(grup)
      n_grup = len(df_grupos)
      # Numero de cupos:
      '''
      n_cupo = df_cupo.sum()
      n_inscritos = df_inscritos_.sum()
      # 
      '''
      departamento.append(dep.rstrip())
      asignaturas.append(n_asg)
      #grupos.append(n_grup)
      '''
      cupos.append(n_cupo)
      inscritos.append(n_inscritos)
      '''
    ASIGNATURAS_OFERTADAS_PERIOD = pd.DataFrame({
        'DEPARTAMENTO':departamento,
        'ASIGNATURAS': asignaturas
        #'GRUPOS': grupos
          })
        #'CUPOS': cupos,
        #'INSCRITOS':inscritos
        
    return ASIGNATURAS_OFERTADAS_PERIOD
  def inscritos_nivel(self,name_sia_asignaturas, tipo_nivel, semestre_actual):
    # tomo pregrado:
    # (poner nivel como una varible):
    df_inscritos  = self.load(name_sia_asignaturas, 1, 0) # CARGAR SIA ANTERIOR
    df_by_nivel = df_inscritos[df_inscritos['TIPO_NIVEL'] == tipo_nivel]
    # selecciono dni set:
    dnis = set(df_by_nivel['DOCUMENTO'].to_list())
    # preparo listas:
    plan_now = []
    cedula_now = []
    apertura_now = []
    plan_before = []
    cedula_before = []
    apertura_before = []
    # para c/u cedulas...
    for cc in dnis:
      # obtengo su "fila"...
      df_estudiante = df_by_nivel[df_by_nivel['DOCUMENTO'] == cc]
      # Si estudiante esta en convocatoria y aperturas semestre actual... (Poner semestre como una variable)
      # solo apertura ... sufiente
      if df_estudiante['CONVOCATORIA'].iloc[0] == semestre_actual and df_estudiante['APERTURA'].iloc[0] == semestre_actual:
        # Obtengo su plan y lo guardo en planes
        plan_now.append(df_estudiante['PLAN'].iloc[0])
        # tambien guardo su cedula:
        cedula_now.append(cc)
        apertura_now.append(df_estudiante['APERTURA'].iloc[0])
      elif df_estudiante['APERTURA'].iloc[0] != semestre_actual:
        plan_before.append(df_estudiante['PLAN'].iloc[0])
        cedula_before.append(cc)
        apertura_before.append(df_estudiante['APERTURA'].iloc[0])

    # guardo en diccionario informacion:
    INSCRITOS_ANTIGUOS = {
        'PLAN': plan_before,
        'CEDULA': cedula_before,
        'APERTURA': apertura_before
    }
    INSCRITOS_NUEVOS = {
        'PLAN': plan_now,
        'CEDULA': cedula_now,
        'APERTURA': apertura_now
    }
    # Escribo como datagrame plan y cedula...
    df_INSCRITOS_ANTIGUOS = pd.DataFrame(INSCRITOS_ANTIGUOS)
    df_INSCRITOS_NUEVOS = pd.DataFrame(INSCRITOS_NUEVOS)
    return [df_INSCRITOS_NUEVOS, df_INSCRITOS_ANTIGUOS]

  def proyectos_tesis(self,name_sia_asignaturas, name_sia_grphor, name_save):
    df_inscritos  = self.load(name_sia_asignaturas, 1, 0) # CARGAR SIA ANTERIOR
    df_hr_gr = self.load(name_sia_grphor, 1, 0)
    df_hr_gr_filtered = df_hr_gr[[
                                'ID_ASSIGNATURA', # id asignatura
                                'NOMBRE_ASS', # nombre asignatura
                                'PPAL_ID_GRUPO_ACTIVIDAD', # id grupo
                                'PPAL_DESC_GRUPO_ACTIVIDAD', # descripcion grupo
                                'PPAL_NUM_INSCRITOS', # numero de inscritos
                                'PPAL_DOC_DOCENTE', # documento docente
                                'PPAL_NOMPRS' # nombre docente
                            ]]
    df_hr_gr_filtered = df_hr_gr_filtered.fillna('') # llenar nan con espacio texto vacio.
    # Columnas necesarias para inscritos
    df_inscritos_filtered = df_inscritos[[
                                        'COD_PLAN', # codigo plan
                                        'PLAN', # plan
                                        'DOCUMENTO', # documento
                                        'NOMBRES', # nombres
                                        'APELLIDOS', # apellidos
                                        'CORREO', # correo
                                        'COD_ASIGNATURA', # cod asignatura
                                        'ASIGNATURA', # asignatura
                                        'GRUPO_ASIGNATURA' # grupo asignatura
                                        ]]
    df_inscritos_filtered = df_inscritos_filtered.fillna('')# llenar nan con espacio texto vacio.
    df_inscritos_filtered['DOCENTE'] = '' # creo una columna que se llame docente...

    list_tesis_proyectos = [
      "TRABAJO FINAL",
      "TRABAJO FINAL DE MAESTRIA",
      "TESIS DE MAESTRIA",
      "PROYECTO DE TESIS DE DOCTORADO",
      "TESIS DE DOCTORADO",
      "TESIS",
      "TRABAJO FINAL DE MAESTRÍA",
      "PROYECTO DE TESIS",
      "TESIS DE MAESTRÍA",
    ]
    index_drop = [] # lista vacia

    # Recorrer por filas a inscritos...
    for index, row in df_inscritos_filtered.iterrows():
      # Tomo codigo de asignatura:
      asignatura = row['COD_ASIGNATURA']
      # Tomo el grupo:
      grupo = row['GRUPO_ASIGNATURA']
      # Busco en grupos y horarios lugares donde coincida asignatura:
      tf_doc_asignatura = df_hr_gr_filtered['ID_ASSIGNATURA'] == asignatura
      # Busco en grupos y horarios lugares donde coincida grupo:
      tf_doc_grupo = df_hr_gr_filtered['PPAL_ID_GRUPO_ACTIVIDAD'] == grupo
      # Busco en horarios y grupos la coincidencia mutua (AND):
      df_docente = df_hr_gr_filtered[tf_doc_asignatura & tf_doc_grupo]
      try:
        # Intento capturar el nombre de la asignatura:
        asg = df_docente['NOMBRE_ASS'].to_list()[0]
        # valido si esa asignatura pertenece a la lista de asignaturas necesarias:
        tf = valid_asignature(asg.upper(), list_tesis_proyectos)
        if tf == True: # si pertenece
        # Se extrae el nombre del docente:
          docente_nombre = df_docente['PPAL_NOMPRS'].to_list()[0]
        # Se lo guarda en la col. creada llamada docente
          row['DOCENTE'] = docente_nombre
        else:
        # Sino entonces guardo indices para dropear
          index_drop.append(index)
      except:
        # Se ven tantos 0 porque es cuando no se encuentran coincidencias 
        # e igual se guarda el indice para dropear:
          print(len(df_docente)) 
          index_drop.append(index)

    # dropeo dataframe con las filas que no tienen la informacion requerida:
    df_inscritos_filtered = df_inscritos_filtered.drop(index_drop)

    list_dfs = [
            (df_inscritos_filtered, 'PRINCIPAL')
              ]
    self.write_engine(list_dfs, name_save)

    return df_inscritos_filtered

  def tutores(self,name_tutores, name_save, name_matriculados):

    df_tutores  = self.load(name_tutores, 1, 1) # CARGAR SIA ANTERIOR
    df_tutores = df_tutores.fillna('')
    planes = set(df_tutores['PLAN'].to_list())

    # Matriculados:
    df_matriculados  = self.load(name_matriculados, 1, 1)
    df_nombres_apellidos = df_matriculados[["NOMBRES", "APELLIDO1", "APELLIDO2"]]
    df_nombres_apellidos["COMPLETO"] = df_nombres_apellidos["NOMBRES"] + " " + df_nombres_apellidos["APELLIDO1"] + " " + df_nombres_apellidos["APELLIDO2"]
    df_nombres_apellidos = df_nombres_apellidos.fillna('')
    df_nombres_apellidos["COMPLETO"] = df_nombres_apellidos["COMPLETO"].str.upper()
    df_nombres_apellidos["COMPLETO"] = df_nombres_apellidos["COMPLETO"].apply(unidecode)
    df_nombres_apellidos["COMPLETO"] = df_nombres_apellidos["COMPLETO"].str.strip()
    matriculados_nombre = list(df_nombres_apellidos["COMPLETO"])

    df_list = []
    todo = []

    for plan in planes:
      # plan i:
      df_matriculados_3 = pd.DataFrame()
      
      try:
        name_estudiantes = "ESTUDIANTES_" + plan + ".xlsx"
        name_estudiantes = name_estudiantes.replace(' ', '_')
        name_estudiantes = os.path.join('sia','subidos',name_estudiantes)
        print(os.path.join(self.path,name_estudiantes))
        df_estudiantes = self.load(name_estudiantes, 0, 0)
        df_estudiantes = df_estudiantes.fillna('')
        df_estudiantes["NOMBRES"] = df_estudiantes["NOMBRES"].str.upper()
        df_estudiantes["NOMBRES"] = df_estudiantes["NOMBRES"].apply(unidecode)
        df_estudiantes["NOMBRES"] = df_estudiantes["NOMBRES"].str.strip()
        df_estudiantes_R = df_estudiantes.loc[df_estudiantes["NOMBRES"].isin(list(matriculados_nombre))]
        nombres_r = list(df_estudiantes_R.NOMBRES)
        df_matriculados_2 = df_matriculados[df_nombres_apellidos["COMPLETO"].isin(nombres_r)]
        df_matriculados_2["APELLIDOS"] = df_matriculados_2["APELLIDO1"] + " " + df_matriculados_2["APELLIDO2"]
        # cambiar nombre cols
        df_matriculados_2["CORREO ESTUDIANTE"] = df_matriculados_2["CORREO"]
        df_matriculados_2["PERIODO_CONVOCATORIA"] = df_matriculados_2["CONVOCATORIA"]
        df_matriculados_2["PERIODO_APERTURA"] = df_matriculados_2["APERTURA"]
        # col intesection
        col_tut = set(df_tutores.columns)
        col_matri = set(df_matriculados_2)
        cc = col_tut.intersection(col_matri)
        df_matriculados_3 = df_matriculados_2[list(cc)]
        
      except:
          print(f"No se encontro {name_estudiantes}")

      df_filtered = df_tutores[df_tutores['PLAN'] == plan]
      df_con_tutor = df_filtered[df_filtered['TUTOR'] != '']
      df_sin_tutor = df_filtered[df_filtered['TUTOR'] == '']
      if plan == 'ADMINISTRACION DE EMPRESAS (N)':
          plan = 'ADMIN EMPRESAS (N)'
      elif plan == 'ADMINISTRACION DE EMPRESAS (D)':
          plan = 'ADMIN EMPRESAS (D)'
      elif plan == 'ADMINISTRACION DE SISTEMAS INFORMATICOS':
          plan = 'ADMIN SISINFO'
      elif plan == 'GESTION CULTURAL Y COMUNICATIVA':
          plan = 'GEST CULT'
      # Matriculados:
      df_con_tutor = df_con_tutor.fillna('')
      df_list.append( (df_con_tutor, plan + ' CT') )
      
      df_concat_sin_tutor = pd.concat([df_sin_tutor, df_matriculados_3])
      df_concat_sin_tutor = df_concat_sin_tutor.fillna('')
      df_concat_sin_tutor["COMPLETOS"] = df_concat_sin_tutor["NOMBRES"] + " " + df_concat_sin_tutor["APELLIDOS"]
      df_arq_st = df_concat_sin_tutor.drop_duplicates(subset=["COMPLETOS"], keep='first')
      df_arq_st = df_arq_st.drop(columns=["COMPLETOS"])
      df_list.append( (df_con_tutor, plan + ' CT') )
      df_list.append( (df_arq_st , plan + ' ST') )
      df_con_tutor["PLAN_TUTOR"] = plan + ' CT'
      df_arq_st["PLAN_TUTOR"] = plan + ' ST'
      todo.append(df_con_tutor)
      todo.append(df_arq_st)
    new_df = pd.concat(todo)
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    print(len(new_df))
    return df_list, new_df

# ============================================================================
# FUNCIONES AUXILIARES:
# ============================================================================
def DNI_2_TotCred(DNI=555, df=pd.DataFrame()):
  try:
    # Cedula:
    informe = df[df['DOCUMENTO'] == DNI]
     # Creditos:
    cred = informe['CREDITOS_ASIGNATURA'].to_list()
    if DNI == '1080040060':
      y = sum(cred)
    if len(cred) != 0:
      return sum(cred) # Suma de creditos.
    else:
      return -1 # Se encontro DNI pero por alguna razon no tiene creditos.
  except KeyError:
    print('No se encuentra col: ' + 'DOCUMENTO')
    return -2 # Sino se encuentra la col. DOCUMENTOS return -> -2
def DNI_2_Feature(DNI=555, feature='DOCUMENTO', df=pd.DataFrame()):
  # Caracteristicas tipo texto:
  string_1_feat = ['SEXO', 'DEPARTAMENTO_NACIMIENTO','DEPARTAMENTO_PROCEDENCIA',
                   'TIPO_NIVEL','CONVOCATORIA','APERTURA']
  # Caracteristicas tipo numero:
  num_1_feat = ['AVANCE_CARRERA']

  # COD_PLAN FALTA -> SALE UNA LISTA y hay que ver si una sola persona tiene un solo COD de plan?
  # FALTA PLAN -> UNA PERSONA PUEDE PERTENECER A UN PLAN O A VARIOS AL MISMO TIEMPO?

  # Cedula:
  try:
    df_buscado = df[df['DOCUMENTO'] == DNI] # Empty DataFrame -> No se encontro documento.
    try:
      # Salida default:
      salida = df_buscado[feature].to_list() # -> salida = []
      # Busqueda texto:
      if feature in string_1_feat:
        if len(salida) == 0:
          salida = 'INDEFINIDO' # No se encontró en df
        else:
          salida = salida[0] # string
        return salida
      # Busqueda numerica:
      elif feature in num_1_feat:
        if len(salida) == 0:
          salida = -5 # No se encontró en df
        else:
          salida = salida[0] # Numero
        return salida
      else:
        return salida[0]
    except KeyError:
      print('No se encuentra col: ' + feature)
      return -2
  except KeyError:
    print('No se encuentra col: ' + 'DOCUMENTO')
    return -2 # Sino se encuentra la col. DOCUMENTOS return -> -2
ALLOWED_EXTENSIONS = {'xlsx', 'pdf', 'txt', 'csv'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def files_in_data(path_servicio):
    # folder path
    dir_path = path_servicio

    # list to store files
    res = []

    # Iterate directory
    for path in os.listdir(dir_path):
        # check if current path is a file
        if os.path.isfile(os.path.join(dir_path, path)):
            res.append(path)
    print(res)
    return res
def valid_asignature(asg, posibilities):
    if asg in posibilities:
        return True
    else:
        return False
# General render informe
def render_informe(upload_folder,sessions):
    path_servicio_upload = os.path.join(upload_folder,sessions['path'],'subidos')
    path_servicio_download = os.path.join(upload_folder,sessions['path'],'generados')
    # lista de archivos:
    files_upload = files_in_data(path_servicio_upload)
    files_download = files_in_data(path_servicio_download)
    # mensaje:
    # Upload menssaje:
    list_check = [elm1 in files_upload for elm1 in sessions['required_files']]
    tf_upload = all(list_check)
    if tf_upload == True:
        Mensaje_Reporte = 'Tienes todos los archivos necesarios.'
    else:
        Mensaje_Reporte = 'No tienes en carpeta los archivos necesarios.'
    # Donwlod mensaje:
    list_check = [elm1 in files_download for elm1 in sessions['download_file']]
    tf_upload = all(list_check)
    if tf_upload == True:
        Mensaje_Descargar = 'Tienes todos los archivos necesarios.'
    else:
        Mensaje_Descargar = 'No tienes en carpeta los archivos necesarios.'
    return render_template( sessions['path_template'],
                            servicio=sessions['servicio'],
                            Mensaje_Reporte = Mensaje_Reporte,
                            Mensaje_Descargar = Mensaje_Descargar,
                            Mensaje_Actualizacion = sessions['msj_actualizacion'],
                            file = sessions['file'],
                            Mensaje_help_1 =  sessions['msjhelp1'],
                            Mensaje_help_2 =  sessions['msjhelp2'],
                            Mensaje_help_3 =  sessions['msjhelp3'],
                            data = sessions['data'],
                            link = sessions['link'])

def normalizacion_col(col_name, df):
  try:
    df = df.fillna('')
    df[col_name] = df[col_name].str.upper()
    df[col_name] = df[col_name].apply(unidecode)
    df[col_name] = df[col_name].str.strip()
  except:
    df = pd.DataFrame()
  return df



    
# Funcion para hacer match:
# esta seccion presenta problemas en sphinx comentarla para que guncione
# path_planes = os.path.join('/home/Analisis/basic-flask-app/src/data','Planes.xlsx')


# Ruta actual donde se encuentra dllcopy.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# Subir dos niveles para llegar al mismo nivel que folderA
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

# Crear la ruta completa al archivo Excel en folderA
path_planes  = os.path.join(project_root, 'data', 'Planes.xlsx')

# path_planes = os.path.join('src/data','Planes.xlsx')




df_planes = pd.read_excel(path_planes)
# crear df nueva:
df_planes['NOMID1'] = df_planes['NOMID1'].str.upper()
df_planes['NOMID1'] = df_planes['NOMID1'].apply(unidecode)
df_nueva = df_planes[['FAC', 'NOMID1']].copy()

# Convertir sintaxis
# Lista de palabras a dejar en minúsculas
# Función para capitalizar las primeras letras y dejar palabras específicas en minúsculas
def capitalize_text(text):
    palabras_a_min = ['y', 'en', 'de', 'la']
    if  isinstance(text, str):
      words = text.split()
      capitalized_words = [word.lower() if word.lower() in palabras_a_min else word.title() for word in words]
      return ' '.join(capitalized_words)
    else:
      return text



# # Función para encontrar el string más cercano
def encontrar_mas_cercano(string,case_match):
  # facultades
  if case_match == 1:
    lista_strings = ['FACULTAD DE INGENIERIA Y ARQUITECTURA',
                     'FACULTAD DE ADMINISTRACION',
                     'FACULTAD DE CIENCIAS EXACTAS Y NATURALES']
    
    try:
      matches = get_close_matches(string, lista_strings)
      #matches = convertir_palabras_iniciales_mayuscula(matches)
      if matches:
        return matches[0]  # Devuelve el primer string más cercano
      else:
        return string  # Si no hay coincidencias, conserva el valor original
    except:
      return ''
  # programas
  elif case_match == 2:
    lista_strings = ['INGENIERIA CIVIL',
                    'INGENIERIA ELECTRICA',
                    'INGENIERIA QUIMICA',
                    'INGENIERIA INDUSTRIAL',
                    'ARQUITECTURA',
                    'ADMINISTRACION DE EMPRESAS (D)',
                    'ADMINISTRACION DE EMPRESAS (N)',
                    'INGENIERIA ELECTRONICA',
                    'ADMINISTRACION DE SISTEMAS INFORMATICOS',
                    'INGENIERIA FISICA',
                    'CONSTRUCCION',
                    'MATEMATICAS',
                    'GESTION CULTURAL Y COMUNICATIVA',
                    'CIENCIAS DE LA COMPUTACION',
                    'ADMINISTRACION DE SISTEMAS INFORMATICOS',
                    'ESPECIALIZACION EN DIRECCION DE PRODUCCION Y OPERACIONES',
                    'ESPECIALIZACION EN GESTION DE REDES DE DATOS',
                    'ESPECIALIZACION EN INGENIERIA AMBIENTAL - AREA SANITARIA',
                    'ESPECIALIZACION EN INGENIERIA FINANCIERA',
                    'ESPECIALIZACION EN VIAS Y TRANSPORTE',
                    'ESPECIALIZACION EN AUTOMATIZACION INDUSTRIAL',
                    'ESPECIALIZACION EN DESARROLLO DE MARKETING CORPORATIVO',
                    'ESPECIALIZACION EN FINANZAS CORPORATIVAS',
                    'ESPECIALIZACION EN GESTION CULTURAL, ENFASIS EN PLANEACION Y POLITICAS CULT',
                    'ESPECIALIZACION EN AUDITORIA DE SISTEMAS',
                    'ESPECIALIZACION EN INGENIERIA HIDRAULICA Y AMBIENTAL',
                    'ESPECIALIZACION EN GERENCIA ESTRATEGICA DE PROYECTOS',
                    'ESPECIALIZACION EN ESTRUCTURAS',
                    'ESPECIALIZACION EN ALTA GERENCIA',
                    'ESPECIALIZACION EN INGENIERIA ELECTRICA',
                    'ESPECIALIZACION EN ESTADISTICA',
                    'ESPECIALIZACION EN ACTUARIA Y FINANZAS',
                    'ESPECIALIZACION EN GEOTECNIA',
                    'ESPECIALIZACION EN BIONEGOCIOS',
                    'ESPECIALIZACION EN LOGISTICA Y CADENAS DE ABASTECIMIENTO',
                    'ESPECIALIZACION EN BIOINGENIERIA',
                    'ESPECIALIZACION EN NANOTECNOLOGIA',
                    'MAESTRIA EN ADMINISTRACION',
                    'MAESTRIA EN CIENCIAS - MATEMATICA APLICADA',
                    'MAESTRIA EN CIENCIAS - FISICA',
                    'MAESTRIA EN HABITAT',
                    'MAESTRIA EN INGENIERIA - INGENIERIA QUIMICA',
                    'MAESTRIA EN MEDIO AMBIENTE Y DESARROLLO',
                    'MAESTRIA EN INGENIERIA - AUTOMATIZACION INDUSTRIAL',
                    'MAESTRIA EN INGENIERIA - INGENIERIA INDUSTRIAL',
                    'MAESTRIA EN ENSENANZA DE LAS CIENCIAS EXACTAS Y NATURALES',
                    'MAESTRIA EN INGENIERIA - INGENIERIA ELECTRICA',
                    'MAESTRIA EN INGENIERIA - INGENIERIA AMBIENTAL',
                    'MAESTRIA EN INGENIERIA - INFRAESTRUCTURA Y SISTEMAS DE TRANSPORTE',
                    'MAESTRIA EN ADMINISTRACION DE SISTEMAS INFORMATICOS',
                    'MAESTRIA EN INGENIERIA - ESTRUCTURAS',
                    'MAESTRIA EN INGENIERIA - RECURSOS HIDRAULICOS',
                    'MAESTRIA EN GESTION CULTURAL',
                    'MAESTRIA EN ARQUITECTURA',
                    'DOCTORADO EN INGENIERIA AUTOMATICA',
                    'DOCTORADO EN INGENIERIA - INDUSTRIA Y ORGANIZACIONES',
                    'DOCTORADO EN INGENIERIA - INGENIERIA QUIMICA',
                    'DOCTORADO EN INGENIERIA - INGENIERIA CIVIL',
                    'DOCTORADO EN ADMINISTRACION',
                    'DOCTORADO EN CIENCIAS - MATEMATICAS',
                    'DOCTORADO EN CIENCIAS - FISICA',
                    'DOCTORADO EN ESTUDIOS AMBIENTALES',
                    'ESPECIALIZACION EN AUTOMATIZACION INDUSTRIAL',
                    'MAESTRIA EN ADMINISTRACION',
                    'MAESTRIA EN INGENIERIA AUTOMATIZACION INDUSTRIAL',
                    'MAESTRIA EN INGENIERIA AUTOMATIZACION INDUSTRIAL',
                    'MAESTRIA EN ADMINISTRACION',
                    'ESPECIALIZACION EN GESTION DE REDES DE DATOS',
                    'MAESTRIA EN CIENCIAS - MATEMATICA APLICADA',
                    'MAESTRIA EN ADMINISTRACION',
                    'MAESTRIA EN ADMINISTRACION',
                    'ESPECIALIZACION EN VIAS Y TRANSPORTE',
                    'ESPECIALIZACION EN GERENCIA ESTRATEGICA DE PROYECTOS',
                    'ESPECIALIZACION EN GERENCIA ESTRATEGICA DE PROYECTOS',
                    'MAESTRIA EN INGENIERIA - INGENIERIA ELECTRICA',
                    'ESPECIALIZACION ALTA GERENCIA',
                    'ESPECIALIZACION EN VIAS Y TRANSPORTE',
                    'ESPECIALIZACION EN INGENIERIA HIDRAULICA Y AMBIENTAL',
                    'ESPECIALIZACION EN ESTRUCTURAS',
                    'ESPECIALIZACION EN FINANZAS CORPORATIVAS',
                    'ESPECIALIZACION EN INGENIERIA HIDRAULICA Y AMBIENTAL']
    try:
      matches = get_close_matches(string, lista_strings)
      #matches = convertir_palabras_iniciales_mayuscula(matches)
      if matches:
        return matches[0]  # Devuelve el primer string más cercano
      else:
        return string  # Si no hay coincidencias, conserva el valor original
    except:
      return ''
    
def fill_empty_spaces(df, columns_to_exclude = [
   "G1", "G2", "G3", "G4", "G5", "G6", "G7", "PBM", "PROM_ACADEMICO_ACTUAL",
   "PAPA_PERIODO", "AVANCE_CARRERA","FECHA"]):
    filled_df = df.copy()
    
    for column in filled_df.columns:
        if column not in columns_to_exclude:
            try:
              filled_df[column] = filled_df[column].apply(lambda x: "Sin Informacion" if pd.isnull(x) or x.strip() == "" else x)
            except:
               pass
    
    return filled_df



# =================== NUEVO REQUERIMIENTO PSL ================================

def asistenciaOriginal_to_estandar_AV(folder_path, rangos):
  files = os.listdir(folder_path)
  file_names = [file for file in files if os.path.isfile(os.path.join(folder_path, file))]
  resultado = extraer_numeros_letras(rangos)
  df_salida = pd.DataFrame()
  for i, file in enumerate(file_names):
      name_psl = os.path.join(folder_path,file)
      tupla, letras = resultado[i]
      df_i = pd.read_excel(name_psl, sheet_name = 1, skiprows = tupla[0], nrows=tupla[1],  usecols= letras)
      print(f"File name = {file} \n con rangos {tupla[0]} - {tupla[1]}")
      resultado_t = re.sub(r'Asistencia_', '', file[:-5])
      df_i["SUB_SERVICIO"] = resultado_t
      df_new = concatenate_information_by_date(df_i)
      # BORRAR
      columns_news = [col.strip().upper() for col in df_new.columns]
      df_new.columns = columns_news
      df_salida = pd.concat([df_salida, df_new])
  # strip colums:
  columns_news = [col.strip().upper() for col in df_salida.columns]
  df_salida.columns = columns_news
  # cambiar oden:2
  df_salida_v2 = df_salida[["FECHA","DOCUMENTO","CORREO","NOMBRES Y APELLIDOS","SUB_SERVICIO", "PROGRAMA","FACULTAD"]]
  # Borrar cuando se quite encuesta:
  for i in range(1,8):
    df_salida_v2[f"G{i}"] = ''
  # agregar 
  df_salida_v2["CEDULA-RI"] = df_salida["PROFESIONAL PSL"]
  df_salida_v2["PERIODO-AT"] = df_salida["PERIODO DE ATENCIÓN"]
  df_salida_v2 = df_salida_v2.rename(columns={"FACULTAD":"MI-FACULTAD"})
  df_salida_v2 = df_salida_v2.rename(columns={"SUB_SERVICIO":"SUBSERVICIO"})
  df_salida_v2 = df_salida_v2.filter(regex='^(?!Unnamed:).', axis=1)
  print("==========================================")
  print(df_salida_v2.info())
  df_salida_v2.reset_index(inplace=True)
  return df_salida_v2
    

def asistenciaOriginal_to_estandar_TIC(file_path, rangos):
  excel_file = pd.read_excel(file_path, sheet_name=None)
  resultado = extraer_numeros_letras(rangos)
  df_salida_2 = pd.DataFrame()
  for i, resultados in enumerate(resultado):
      tupla, letras = resultados
      print(f'Tupla de números: {tupla}, String de letras: {letras}')
      keys = list(excel_file.keys())
      key_i = keys[i]
      #df_i = excel_file[key_i]
      df_new = pd.read_excel(file_path, key_i, skiprows = tupla[0], nrows=tupla[1], usecols=letras)
      df_new = concatenate_information_by_date(df_new)
      df_new["SUB_SERVICIO"] = key_i
      print(f"Hoja = {key_i}")
      print(f"Asistencias = {len(df_new)}")
      print("\n")
      df_salida_2 = pd.concat([df_salida_2, df_new])
  # strip colums:
  
  columns_news = [col.strip().upper() for col in df_salida_2.columns]
  df_salida_2.columns = columns_news
  # cambiar oden:2
  df_salida_v2 = df_salida_2[["FECHA","NOMBRES Y APELLIDOS","CORREO","DOCUMENTO", "PROGRAMA","ASIGNATURA","NOTA FINAL"]]
  df_salida_v2["PRODUCTO"] = ""
  # Borrar cuando se quite encuesta:
  for i in range(1,6):
    df_salida_v2[f"G{i}"] = ''
  # agregar
  df_salida_v2["NOMBRE-RE"] = df_salida_2["DOCENTE TITULAR"]
  df_salida_v2["CODIGO ASIGNATURA"] = ""
  df_salida_v2["CORREO-RE"] = ""
  df_salida_v2["CEDULA-RI"] = df_salida_2["PROFESIONAL PSL"]
  df_salida_v2["TIPO-RI"] = ""
  df_salida_v2["PERIODO-AT"] = df_salida_2["PERIODO DE ATENCIÓN"]
  df_salida_v2 = df_salida_v2.rename(columns={"NOTA FINAL":"NOTA"})
  df_salida_v2.reset_index(inplace=True)
  df_salida_v2 = df_salida_v2.filter(regex='^(?!Unnamed:).', axis=1)
  print("==========================================")
  print(df_salida_v2.info())
  return df_salida_v2


def extraer_numeros_letras(rangos):
    resultados = []
    for rango in rangos:
        # Utilizamos expresiones regulares para extraer los números y las letras
        match = re.match(r'([A-Z]+)(\d+):([A-Z]+)(\d+)', rango)
        if match:
            # Extraemos los grupos de la expresión regular
            letras_inicio, numero_inicio, letras_fin, numero_fin = match.groups()
            # Convertimos los números a enteros
            numero_inicio = int(numero_inicio)
            numero_fin = int(numero_fin)
            # Creamos las tuplas y el string de letras
            tupla_numeros = (numero_inicio-1, numero_fin-1)
            string_letras = f'{letras_inicio}:{letras_fin}'
            resultados.append((tupla_numeros, string_letras))
    return resultados


# Esta funcion recibe df...
def concatenate_information_by_date(df):
    # Primero identificar columnas tipo fecha y columnas "normales"
    columnas_dates = []
    columnas_otras = []
    count = 0
    for col in df.columns:
    # utilizando la funcion find_date_datetime identificar si la columna es tipo fecha.
        tf_date = find_date_datetime(col)
        # identificar si la columna del df es de fecha:
        if tf_date == 1:
            columnas_dates.append(col)
            count += 1
        else:
            columnas_otras.append(col)
    print(f"Cantidad de columnas tipo fecha = {count}")
    print(columnas_dates)
    # Crear una dataframe para concatenar por hoja.
    new_df = pd.DataFrame(columns = ['FECHA'] + columnas_otras)
    # Por cada columna de fecha...
    for col_date in columnas_dates:
        # Iterar sobre las filas de df
        for index, row in df.iterrows():
            # Identificar la asistencia:
            campo_asistencia = row[col_date]
            try:
                campo_asistencia = campo_asistencia.strip()
                campo_asistencia = campo_asistencia.upper()
                campo_asistencia = unidecode(campo_asistencia)
            except:
                pass
            if campo_asistencia == 'SI':
                # Crear diccionario vacio para concatenar valores por fila:
                dict_to_append = {}
                for col_new_df in new_df.columns:
                    # como FECHA no esta en los datos originales de debe identificar para ponerla.
                    if col_new_df != 'FECHA':
                        dict_to_append[col_new_df] = [row[col_new_df]]
                    else:
                        dict_to_append[col_new_df] = [col_date]
                # concatenar:
                df_row = pd.DataFrame(dict_to_append)
                #new_df = new_df.append(dict_to_append, ignore_index=True)
                new_df = pd.concat([df_row, new_df], axis=0)
    # devolver hoja concatenada:
    return new_df


import datetime

# Funcion para identificar las fechas en las columnas:
def find_date_regular_expresion(col, re_expre = r"\b(\d{2})/(\d{2})/(\d{4})\b"):
    matches = re.findall( re_expre, col)
    fecha = -1
    for match in matches:
        fecha = "/".join(match)
    return fecha
  
def find_date_datetime(col):
    if isinstance(col, datetime):
        return 1
    else:
        return 0
      
      
  
# =================== NUEVO REQUERIMIENTO STEM ================================

# Proceso para capacitaciones:
# ==================================

# Función para limpiar y formatear texto
def limpiar_y_formatear(texto):
    if pd.isna(texto):
        return texto
    # Eliminar espacios en blanco a los lados
    texto = texto.strip()
    # Poner en formato Capitalize
    texto = texto.upper()
    # Eliminar acentos
    texto = unidecode(texto)
    return texto
  
# Lista de palabras a buscar
palabras_buscar = ["BOGOTA", "MEDELLIN", "MANIZALES", "PAZ", "PALMIRA", "TUMACO"]

# Convertir la lista a minúsculas para búsqueda sin distinción de mayúsculas
palabras_buscar = [unidecode(palabra.lower()) for palabra in palabras_buscar]

# Función para limpiar y formatear texto
def limpiar_y_formatear_v2(texto):
    if pd.isna(texto):
        return texto
    # Eliminar espacios en blanco a los lados
    texto = texto.strip()
    # Eliminar acentos
    texto = unidecode(texto)
    # Convertir todo el texto a minúsculas para comparación
    texto_minusculas = texto.lower()
    
    # Buscar la palabra después de "SEDE"
    match_sede = re.search(r'\bSEDE\b\s+(\w+)', texto_minusculas, re.IGNORECASE)
    if match_sede:
        palabra_siguiente = match_sede.group(1).capitalize()
        return palabra_siguiente
    
    # Buscar en la lista de palabras
    for palabra in palabras_buscar:
        if palabra in texto_minusculas:
            return palabra.capitalize()
    
    # Si no se encuentra "SEDE" ni ninguna palabra de la lista, devolver el texto original
    return texto.capitalize()
  
def main_capacitaciones(path_capacitaciones):
  # LOAD:
  #path_capacitaciones = os.path.join('data/Valoración del capacitación (respuestas).xlsx')
  
  df_capacitaciones = pd.read_excel(path_capacitaciones)
  # ETL:
  # Buscar columnas concatenadas:
  mask = df_capacitaciones.iloc[:, 1:].isna().all(axis=1) & df_capacitaciones.iloc[:, 0].notna()

  # crear la fecha llena:
  df_capacitaciones['CAPACITACION'] = df_capacitaciones['Marca temporal'].where(mask).ffill()

  # quitar las filas concatenadas:
  df_capacitaciones_wo_combined = df_capacitaciones[~mask]

  # cambiar nombre de columnas
  # Renombrar columnas específicas
  df_capacitaciones_wo_combined.rename(columns={'Marca temporal': 'FECHA',
                    'Nombre completo': 'NOMBRES Y APELLIDOS',
                    'Correo':'CORREO',
                    'Sede a la que pertenece o perteneció (o en su defecto, lugar de residencia)': "SEDE"},
            inplace=True)

  # llenar NaNs 
  df_capacitaciones_wo_combine = df_capacitaciones_wo_combined.fillna("Sin Informacion")

  # crear documentos
  # Generar una lista de IDs únicos para los valores nulos
  null_ids = ['Null-Cap-ID-' + str(i).zfill(4) for i in range(1, len(df_capacitaciones_wo_combine)+1)]
  df_capacitaciones_wo_combine["DOCUMENTO"] = null_ids


  # Aplicar la función a la columna de texto
  df_capacitaciones_wo_combine['SEDE_CAPACITACION'] = df_capacitaciones_wo_combine['SEDE'].apply(limpiar_y_formatear)

  df_capacitaciones_wo_combine['SEDE_CAPACITACION_3'] = df_capacitaciones_wo_combine['SEDE'].apply(limpiar_y_formatear_v2)
  
  # PROCESO PARA CONCATENAR CON MAIN
  df_capacitaciones_wo_combine = df_capacitaciones_wo_combine.drop(columns=["SEDE_CAPACITACION"])

  # Renombrar columnas específicas
  df_capacitaciones_wo_combine.rename(columns={'SEDE_CAPACITACION_3': 'SEDE_CAPACITACION',
                    'CAPACITACION': "SERVICIO",
                    "CORREO":"CORREO_GENERAL"},
            inplace=True)

  df_capacitaciones_wo_combine["ROL_PRINCIPAL"] = "CAPACITACIONES"
  # Nuevos nombres para las columnas 3, 4 y 5
  nuevos_nombres = {4: 'ENCUESTA_CAP_1',
                    5: 'ENCUESTA_CAP_2',
                    6: 'ENCUESTA_CAP_3',
                    7: 'ENCUESTA_CAP_4',
                    8: 'ENCUESTA_CAP_5'}

  # Crear un diccionario para mapear los nombres antiguos a los nuevos usando sus índices
  rename_dict = {df_capacitaciones_wo_combine.columns[idx]: nuevos_nombres[idx] for idx in nuevos_nombres}

  # Renombrar las columnas
  df_capacitaciones_wo_combine.rename(columns=rename_dict, inplace=True)
  
  # quitar sede
  df_capacitaciones_wo_combine = df_capacitaciones_wo_combine.drop(columns=["SEDE"])
  
  return df_capacitaciones_wo_combine

# Proceso para datos manuales:
# ==================================

# Función para obtener el número de asistentes de una expresión
def obtener_numero_asistentes(expresion):
    match = re.search(r'\d+', expresion)  # Buscar el número en la expresión
    if match:
        return int(match.group())  # Devolver el número encontrado
    return 0

def main_manuales(path):
  # LOAD:
  #path = "data/Asistencias Físicas 2024-1S.xlsx"
  df = pd.read_excel(path, sheet_name=0, header=1)
  
  # Idenficar capacitaciones
  # Crear un DataFrame df_nan con filas que tienen NaN en la columna 'Nombre'
  df_capacitaciones = df[df['Nombre'].isna()]
  # Eliminar filas con NaN en la columna 'Nombre' del DataFrame original
  df = df.dropna(subset=['Nombre'])
  
  # Selecionar asistentes:
  # Seleccionar filas que contienen la expresión "asistente"
  df_asistentes = df[df['Nombre'].str.contains('asistente')]
  
  # Seleccionar "Normales":
  df_normal = df[~df['Nombre'].str.contains('asistente')]
  # tratamiento de Normales:
  # Crear una copia de normal:
  df_normal_v2 = df_normal.copy()

  # Convertir la columna de fecha a datetime
  df_normal_v2['Fecha'] = pd.to_datetime(df_normal_v2['Fecha'], errors='coerce')

  # Llenar los NaN hacia adelante
  df_normal_v2['Fecha'] = df_normal_v2['Fecha'].fillna(method='ffill')

  # Generar una lista de IDs únicos para los valores nulos
  null_ids = ['Null-' + str(i).zfill(4) for i in range(1, df_normal['Documento'].isnull().sum() + 1)]

  # Asignar los IDs a los valores nulos en la columna 'Documento'
  df_normal_v2.loc[df_normal['Documento'].isnull(), 'Documento'] = null_ids

  # Llenar valores Nan
  df_normal_v2 = df_normal_v2.fillna("Sin Informacion")
  
  # Tratamiento a df_asistentes:
  # Obtener el número de asistentes y replicar las filas
  nuevas_filas = []
  for index, row in df_asistentes.iterrows():
      num_asistentes = obtener_numero_asistentes(row['Nombre'])
      if num_asistentes > 0:
          for _ in range(num_asistentes):
              nueva_fila = row.copy()  # Copiar la fila
              nueva_fila['Nombre'] = 'Sin Informacion'  # Reemplazar la columna 'Nombre'
              nuevas_filas.append(nueva_fila)

  # Crear un nuevo DataFrame con las filas replicadas
  df_nuevas_filas = pd.DataFrame(nuevas_filas)

  # Generar una lista de IDs únicos para los valores nulos
  null_ids = ['Null_asist-' + str(i).zfill(4) for i in range(1, len(df_nuevas_filas) + 1)]

  # Asignar los IDs a los valores nulos en la columna 'Documento'
  df_nuevas_filas['Documento'] = null_ids

  # Llenar values de NAN
  df_nuevas_filas = df_nuevas_filas.fillna("Sin Informacion")

  # Reemplazar expresion:
  df_nuevas_filas = df_nuevas_filas.replace('--', 'Sin Informacion')
  
  # Exportar:
  df_stem_datos_manuales = pd.concat([df_normal_v2, df_nuevas_filas])
  df_stem_datos_manuales = df_stem_datos_manuales.replace('--', 'Sin Informacion')
  # Poner columnas mayusculas
  df_stem_datos_manuales.columns = df_stem_datos_manuales.columns.str.upper()
  # Renombrar columnas específicas
  df_stem_datos_manuales.rename(
            columns={'CATEGORIA FORMULARIO': 'ROL_PRINCIPAL',
                    'NOMBRE': 'NOMBRES Y APELLIDOS',
                    'INSTITUCIÓN':'INSTITUCION',
                    'CATEGORÍA': "CATEGORIA_MANUALES",
                    "CORREO":"CORREO_GENERAL",
                    "SERVICIO UTILIZADO": "SERVICIO",
                    "PROGRAMA CURRICULAR":"PROGRAMA"},
            inplace=True)
  # mapeo para que funcione con MAIN
  df_stem_datos_manuales["ROL_PRINCIPAL"] = df_stem_datos_manuales["ROL_PRINCIPAL"].str.strip()
  # Definimos el diccionario de mapeo
  mapeo_categorias = {
      'Universidad': 'Universidad',
      'Colegio': 'Colegio Estudiantes',
      'Sin Informacion': 'Sin Informacion',
      'Docentes': 'Docentes',
      'Empresa': 'Empresa/Emprendedor',
      'Otra institución': 'Otra Institución',
      'Profesionales otra institución': 'Otra Institución',
      'Profesionales Otras Universidades': 'Otra Institución',
      'Otra Institución ': 'Otra Institución'  # Nota el espacio extra al final
  }
  df_stem_datos_manuales["ROL_PRINCIPAL"] = df_stem_datos_manuales["ROL_PRINCIPAL"].replace(mapeo_categorias)
  
  return df_stem_datos_manuales
  
  
# Proceso para datos "Normales" provenientes de google drive:
# ============================================================

# Función para fusionar las columnas
def fusionar_filas(row):
		valores = row.dropna().values
		if len(valores) == 0:
				return "Sin Informacion"
		else:
				return valores[0]
		

def main_stem(path_file):
		# LOAD DATA and CHANGE COLUMNAES
		df_general = pd.read_excel(path_file,
										usecols='A, B, C, D, E')
		df_general.columns = ["FECHA", 'CORREO_GENERAL', "NOMBRES Y APELLIDOS", "DOCUMENTO", "ROL_PRINCIPAL"]


		df_universidad = pd.read_excel(path_file,
										usecols='F, G, H, I, J, K')
		df_universidad.columns = ["ROL_UNIVERSIDAD", "INSTITUCION", "PROGRAMA", "CORREO", "MUNICIPIO", "SERVICIO"]


		df_empresa = pd.read_excel(path_file,
										usecols='L, M, N, O, P')
		df_empresa.columns = ["INSTITUCION", "CORREO", "MUNICIPIO", "SER_PARTE_EMPRESA", "NECESIDAD_EMPRESA"]


		df_colegio = pd.read_excel(path_file,
										usecols='Q,R,S,T')
		df_colegio.columns = ["INSTITUCION", "MUNICIPIO", "SERVICIO", "ENCUESTA_COLEGIO"]

		df_otra_ie = pd.read_excel(path_file,
										usecols='U, V, W')
		df_otra_ie.columns = ["INSTITUCION", "CORREO", "SERVICIO"]


		df_docentes = pd.read_excel(path_file,
										usecols='X, Y, Z, AA')
		df_docentes.columns = ["CORREO", "INSTITUCION", "MUNICIPIO", "SERVICIO"]
		
		# Find unique columns
		dfs_list = [df_general, df_universidad, df_empresa, df_colegio, df_otra_ie, df_docentes]
		list_colums = []
		for df in dfs_list:
				columns_df = list(df.columns)
				list_colums = list_colums + columns_df
		columnas_unicas = set(list_colums)
		columns_dict = {}
		for df in dfs_list:
				# Iterate over the columns in each DataFrame
				for col_unique in columnas_unicas:
						if col_unique in columns_dict and col_unique in list(df.columns):
								# Si la columna está en las columnas unicas y ademas ya se habia guardado en el diccionario
								# entonces concatenarlo con los valores existentes
								columns_dict[col_unique] = pd.concat([columns_dict[col_unique], df[col_unique]], axis=1)
						elif col_unique in list(df.columns):
								# Si no estaba entonces crear la nueva columna:
								columns_dict[col_unique] = df[[col_unique]]
				else:
						pass
		df_fusion_def = pd.DataFrame()
		columns_name = []
		for key in columns_dict:
				df = columns_dict[key]
				df_fusion = df.apply(fusionar_filas, axis=1)
				df_fusion_def  =  pd.concat([df_fusion_def ,df_fusion], axis=1)
				columns_name.append(key)
		df_fusion_def.columns = columns_name
		return df_fusion_def
	

# Función para identificar la categoría de intitucion:
def identificar_categoria(texto):
		if re.search(r'\bCHEC\b', texto, flags=re.IGNORECASE):
				return 'CHEC'
		elif re.search(r'\bNACIONAL|\bUN\b|\bUNAL\b', texto, flags=re.IGNORECASE):
				return 'Universidad Nacional de Colombia'
		elif re.search(r'\bLUIS AMIGO\b', texto, flags=re.IGNORECASE):
				return 'Luis Amigo'
		else:
				return texto
			
# Función para identificar la categoría municipio
def obtener_primera_palabra(texto):
	# Dividir la cadena en palabras (separadas por espacio o guión)
	if texto != "SIN INFORMACION":
		#print(texto)
		palabras = texto.split() if ' ' in texto else texto.split('-')
		return palabras[0]
	else:
		return texto
	
def capitalize_text(text):
		palabras_a_min = ['y', 'en', 'de', 'la']
		if  isinstance(text, str):
			words = text.split()
			capitalized_words = [word.lower() if word.lower() in palabras_a_min else word.title() for word in words]
			return ' '.join(capitalized_words)
		else:
			return text

def main_ETL(name_load):
  # path formultario:
  #name_load = os.path.join('data/Registro General Aula STEM Centro de Prototipado 2024-1S (respuestas).xlsx')

  # Efectuar proceso de llevar a tabla:
  df_ppl = main_stem(name_load)

  # Poner campo en vacio:
  df_ppl["CEDULA-RI"] = "Sin Informacion"

  # Mofidicacion de institución:
  # =====================================
  # Caso particular revisar o borrar
  df_ppl["INSTITUCION"] = df_ppl["INSTITUCION"].replace(12, '')
  # quitar acento
  df_ppl["INSTITUCION_2"] = df_ppl["INSTITUCION"].apply(unidecode)
  # Mayusculas y quitar espacios en blanco
  df_ppl["INSTITUCION_2"] = df_ppl["INSTITUCION_2"].str.upper().str.strip() 
  # Aplicar la función y crear la columna 'CATEGORIA'
  df_ppl["INSTITUCION"] = df_ppl["INSTITUCION_2"].apply(identificar_categoria)
  # Poner capitalizacion
  df_ppl["INSTITUCION"] = df_ppl["INSTITUCION"].apply(capitalize_text)

  # Mofidicacion de municipio:
  # =====================================
  # Caso particular revisar o borrar
  df_ppl["MUNICIPIO"] = df_ppl["MUNICIPIO"].replace(12, '')
  # quitar acento
  df_ppl["MUNICIPIO_2"] = df_ppl["MUNICIPIO"].apply(unidecode)
  # Mayusculas y quitar espacios en blanco
  df_ppl["MUNICIPIO_2"] = df_ppl["MUNICIPIO_2"].str.upper().str.strip()
  # Aplicar la función y crear la columna 'CATEGORIA'
  df_ppl["MUNICIPIO"] = df_ppl["MUNICIPIO_2"].apply(obtener_primera_palabra)
  # Poner capitalizacion
  df_ppl["MUNICIPIO"] = df_ppl["MUNICIPIO"].apply(capitalize_text)

  # Poner fecha reporte:
  df_ppl["PERIODO_REP"] = '2024-1S'
  
  return df_ppl

def concatenar_stem(df_formulario, df_manuales, df_capacitaciones):
  df = pd.concat([df_formulario, df_manuales, df_capacitaciones], ignore_index=True)
  df = df.fillna("Sin Informacion")
  df["PERIODO_REP"] = '2024-1S'
  return df



# =================== GESTION CURRICULAR ================================
cols_hoja_1_oficial = ['PROGRAMA',
'NIVEL',
'FACULTAD',
'ACTIVO',
'VIGENTE',
'CREACION',
'DOCUMENTO_CREACIÓN',
'APERTURA',
'PRIMERA_COHORTE',
'ACREDITADO_ACTUALMENTE',
'ACREDITABLE',
'RESOLUCIÓN_DE_ACREDITACIÓN_VIGENTE',
'FECHA_ACREDITACIÓN',
'AÑOS_ACREDITACIÓN_OTORGADOS',
'VENCIMIENTO_ACREDITACIÓN',
'Levantamiento de información',
'Aplicación de encuestas',
'Análisis de Información',
'Construcción de juicios de valor',
'Taller de Autoevaluación',
'Formulación del plan de mejoramiento',
'Aval de Consejo de Facultad',
'Radicación ante el Consejo Nacional de Acreditación',
'Visita de Evaluación Externa',
'Informe Preliminar de Pares',
'Resolución de Acreditación',
'PORCENTAJE_TOTAL',
'PERIODO_REPORTE',
'URL',
'EN_EAFA',
'ACREDITACIÓN_ESTADO']

cols_hoja_2_oficial = ['PROGRAMA',
'NIVEL',
'FACULTAD',
'ACTIVO',
'VIGENTE',
'CREACION',
'DOCUMENTO_CREACIÓN',
'APERTURA',
'PRIMERA_COHORTE',
'ACREDITADO_ACTUALMENTE',
'ACREDITABLE',
'RESOLUCIÓN_DE_ACREDITACIÓN_VIGENTE',
'FECHA_ACREDITACIÓN',
'AÑOS_ACREDITACIÓN_OTORGADOS',
'VENCIMIENTO_ACREDITACIÓN',
'Levantamiento de información',
'Aplicación de encuestas',
'Análisis de Información',
'Construcción de juicios de valor',
'Taller de Autoevaluación',
'Formulación del plan de mejoramiento',
'Aval de Consejo de Facultad',
'Radicación ante el Consejo Nacional de Acreditación',
'Visita de Evaluación Externa',
'Informe Preliminar de Pares',
'Resolución de Acreditación',
'PORCENTAJE_TOTAL',
'PERIODO_REPORTE',
'URL',
'EN_EAFA',
'ACREDITACIÓN_ESTADO']

porcentajes = {
    'Levantamiento de información': 0.15,
    'Aplicación de encuestas de percepción': 0.10,
    'Análisis de información': 0.15,
    'Juicios de valor': 0.10,
    'Taller de Autoevaluación': 0.05,
    'Formulación plan de mejoramiento': 0.15,
    'Aval Consejo de Facultad': 0.04,
    'Radicación ante el Consejo Nacional de Acreditación': 0.04,
    'Visita de Evaluación Externa': 0.15,
    'Informe Preliminar de Pares': 0.05,
    'Resolución de Acreditación': 0.02
}

from datetime import datetime # OJO CON ESTO

def main_autoeval(path_file_principal, df_historico):
  
  df_principal = pd.read_excel(path_file_principal, header=0, sheet_name=0)
  # trasnformación de columnas hoja 1:
  df_principal = df_principal.drop(columns=["APERTURA PROCESO DE AUTOEVALUACIÓN (ELIMINAR)"])
  # poner la fecha de hoy en periodo reporte:
  # Obtener la fecha de hoy como cadena en el formato deseado (por ejemplo, '2023-11-20')
  today_date_str = datetime.now().strftime('%Y-%m-%d')
  df_principal['PERIODO_REPORTE'] = today_date_str
  df_principal.columns = cols_hoja_1_oficial

  df_principal["FECHA_ACREDITACIÓN"] = pd.to_datetime(df_principal["FECHA_ACREDITACIÓN"])
  df_principal["FECHA_ACREDITACIÓN"] = df_principal["FECHA_ACREDITACIÓN"].dt.strftime('%Y-%m-%d')

  df_principal["VENCIMIENTO_ACREDITACIÓN"] = pd.to_datetime(df_principal["VENCIMIENTO_ACREDITACIÓN"])
  df_principal["VENCIMIENTO_ACREDITACIÓN"] = df_principal["VENCIMIENTO_ACREDITACIÓN"].dt.strftime('%Y-%m-%d')
  
  for row in range(len(df_principal)):
    row_itr = df_principal.iloc[row,:]
    s = 0
    for key in porcentajes:
        try: 
            if int(row_itr[key]) == 1:
                s += porcentajes[key]
        except:
            pass
    df_principal['PORCENTAJE_TOTAL'][row] = int(round(s,3)*100)
    
  df_historico = pd.concat([df_principal, df_historico], ignore_index=True)
  
  return df_principal, df_historico


# ==================================================
# ===========     SEDE   ===========================
# ==================================================


import os 
import pandas as pd
import gspread
from unidecode import unidecode
import hashlib
from functools import reduce

def hash_column(value):
    """Esta funcion permite tomar un valor (value)
    y hacer un hash con el fin de codificar dicho valor
    en un unico valor.
    """
    return hashlib.sha256(value.encode()).hexdigest()

def set_level_2(df, df_planes):
    """
    Esta funcion permite tomar un dataframe (df) y en funcion de la columna
    PLAN buscar en el dataframe de planes (df_planes) el nivel al que el programa
    pertenece. Por nivel se entiende: PREGRADO, POSGRADO, MAESTRIA, ESPECIALIZACION
    o DOCTORADO.

    :rerurn: df (Modificacion del df de entrada con la nueva columna NIVEL_2)
    """
    df["NIVEL_2"] = ""
    df['PLAN'] = df['PLAN'].str.strip()
    # Por cada una de las filas...
    for i,row in enumerate(df["PLAN"]):
        # Seleccionar plan:
        plan = row
        # Quitar acento y poner en mayuscula:
        plan =  unidecode(plan).upper()
        # Encontrar nivel con plan:
        mask = df_planes['NOMID1'] == plan
        nivel = df_planes.loc[mask, 'COD NIVEL']
        try:
            # Reemplazar:
            df["NIVEL_2"][i] = str(list(nivel)[0])
        except:
            pass
    return df

def crear_avance(df):
    """Esta funcion toma la columna de df AVANCE_CARRERA y en funcion de su valor
    ubica una categoria proveniente de la lista <etiquetas> en una nueva columna
    denominada AVANCE_HISTOGRAMA con el fin de crear valores para hacer un histograma con el avance.

    :rerurn: df (modificacion de df de entrada con la nueva columna AVANCE_HISTOGRAMA)
    """
    # Definir los límites de los rangos
    rangos = [-0.01, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    # Definir las etiquetas correspondientes a los rangos
    etiquetas = ['0-5', '5.1-10', '10.1-15', '15.1-20', '20.1-25', '25.1-30', '30.1-35', '35.1-40', '40.1-45', '45.1-50',
                '50.1-55', '55.1-60', '60.1-65', '65.1-70', '70.1-75', '75.1-80', '80.1-85', '85.1-90', '90.1-95', '95.1-100']
    # Crear la nueva columna con las etiquetas
    df['AVANCE_HISTOGRAMA'] = pd.cut(pd.to_numeric(df['AVANCE_CARRERA'], errors='coerce'), bins=rangos, labels=etiquetas)
    df['AVANCE_HISTOGRAMA'] = df['AVANCE_HISTOGRAMA'].astype(str)
    df['AVANCE_HISTOGRAMA'] = df['AVANCE_HISTOGRAMA'].str.replace('nan','')
    return df


def causa_bloq(strr):
    """Esta función permite ingresar un string proveniente de la causa de bloqueo, quitarle los espacios en blanco.
    y resumir su texto.

    :return: s (string de entrada modificado)
    """
    s = strr.strip()
    if s == 'No disponer de cupo de créditos suficiente para inscribir las asignaturas pendientes de aprobación':
        s = "No disponer de cupo creditos suficientes"
    elif s == 'Obtener dos calificaciones de Reprobado en actividades académicas diferentes a las asignaturas':
        s = 'Dos actividades academicas reprobradas'
    elif s == 'Presentar un Promedio Aritmético Ponderado Acumulado (PAPA) menor que tres punto cinco (3.5)':
        s = "PAPA menor a 3.5."
    elif s == 'Presentar un Promedio Aritmético Ponderado Acumulado menor que tres punto cero (3.0)':
        s = "PAPA menor a 3.0."
    elif s == 'Retiro por superar el tiempo máximo de permanencia permitido en el Posgrado.':
        s = "Supera tiempo maximo de permanencia."
    return s


## Inicializar la clase:
# src\data\sede\subidos
PATH_PRINCIPAL = os.path.join('/home/Analisis/basic-flask-app/src/data', 'sede', 'subidos') # SERVER
MODEL_ADMIN = ExcelPreprocessMain(PATH_PRINCIPAL)

def inicializador_cols(PATH_PRINCIPAL_2, name_activos2, name_bloq_admin, name_bloq_academ, name_planes):  
  # III. CARGAR COLUMNAS:
  # Columnas hoja 1 (MATRICULADOS):
  #PATH_PRINCIPAL_2 = os.path.join('data','2022-2S')
  MODEL_ADMIN_2 = ExcelPreprocessMain(PATH_PRINCIPAL_2)
  # cargar reporte 2022-2S
  #name_activos2 = os.path.join('FACULTADES_MAIN_2022_2S.xlsx') 
  # cargar df de matriculados
  df_mat_2022 = MODEL_ADMIN_2.load(name_activos2, 0, 0) 
  col_out_main = df_mat_2022.columns.to_list()

  # Columnas hoja 2 (Bloq. causas administrativas)
  #PATH_PRINCIPAL_2 = os.path.join('data','2022-2S')
  #MODEL_ADMIN_2 = ExcelAdmin(PATH_PRINCIPAL_2)
  # cargar reporte 2022-2S
  #name_activos2 = os.path.join('FACULTADES_BLOQUEADOS_ADMINISTRATIVAS.xlsx')
  # cargar df de bloq. causas administrativas:
  df_activos2 = MODEL_ADMIN_2.load(name_bloq_admin, 0, 0) 
  col_out_hoja_2 = df_activos2.columns.to_list()

  # Columnas hoja 3 (Bloq. causas academicas)
  #PATH_PRINCIPAL_2 = os.path.join('data','2022-2S')
  #MODEL_ADMIN_2 = ExcelAdmin(PATH_PRINCIPAL_2)
  # cargar reporte 2022-2S
  # name_activos2 = os.path.join('FACULTADES_BLOQUEADOS_ACADEMICAS.xlsx')
  # cargar df de bloq. causas academicas:
  df_activos2 = MODEL_ADMIN_2.load(name_bloq_academ,0, 0) 
  col_out_hoja_3 = df_activos2.columns.to_list()
  
  # Cargar base de datos planes sede (Generado por Vicente Ortega):
  if name_planes is not None:
      df_planes = MODEL_ADMIN_2.load(name_planes, 0, 0)
  else:
      df_planes = ""
  
  return col_out_main, col_out_hoja_2, col_out_hoja_3, df_planes

def load_data_sede(name_activos, name_pav_pap, name_mat_per, name_est_bloq, name_matr_ant):
    # Cargar base de datos activos (generado desde SIA):
    if name_activos is not None:
        df_activos = MODEL_ADMIN.load(name_activos, 1, 1)
    else:
        df_activos = ""

    # Cargar reporte matriculados con avance (generado desde SIA)
    if name_pav_pap is not None:
        df_pav_pap = MODEL_ADMIN.load(name_pav_pap, 1, 1)
    else:
        df_pav_pap = ""

    # Cargar reporte matriculados (generado desde SIA)
    if name_mat_per is not None:
        df_mat_per = MODEL_ADMIN.load(name_mat_per, 1, 0)
    else:
        df_mat_per = ""

    # Cargar bloquados por causas administrativas (generado desde SIA)
    if name_est_bloq is not None:
        df_est_bloq = MODEL_ADMIN.load(name_est_bloq, 0, 0)
    else:
        df_est_bloq = ""

    # Cargar bloquados por causas academicas
    if name_matr_ant is not None:
        df_matriculados_ant = MODEL_ADMIN.load(name_matr_ant, 1, 0)
    else:
        df_matriculados_ant = ""

    return df_activos, df_pav_pap, df_mat_per, df_est_bloq, df_matriculados_ant

"""
def preprocessing_sede(df_planes, df_activos, df_pav_pap, df_mat_per):
  # Procesar planes en la columna Nombre de Plan ('NOMID1'):
  # quitar tildes, espacios en blanco y poner todo en Mayusculas.
  df_planes['NOMID1'] = df_planes['NOMID1'].apply(unidecode)
  df_planes['NOMID1'] = df_planes['NOMID1'].str.strip()
  df_planes['NOMID1'] = df_planes['NOMID1'].str.upper()


  # Generar columna ID con el docigo de plan y documento de activos:
  df_activos["ID"] = df_activos["COD_PLAN"].astype(str) + "-" + df_activos["DOCUMENTO"].astype(str)
  # Seleccionar ID y discapacidad unicamente:
  df_activos_discap = df_activos[["ID","DISCAPACIDAD"]]


  # tomar de matriculados con avane, el codigo de plan, documento y avance de carrera:
  df_pav_pap_v2 = df_pav_pap[["COD_PLAN", "DOCUMENTO", "AVANCE_CARRERA"]]
  # crear columna ID:
  df_pav_pap_v2["ID"] = df_pav_pap_v2["COD_PLAN"].astype(str) + "-" + df_pav_pap_v2["DOCUMENTO"].astype(str)


  # Quitar las siguientes columnas de matriculados:
  cols_drop = [
      "FECHA_CARGA_PREINSCRIPCION",
      "CARNET_UN",
      "NUMERO_HIJOS",
      "INGRESOS_FAMILIARES",
      "PENSION_COLEGIO",
      "CARACTER_COLEGIO",
      "ESTRATO_VIVIENDA",
      "LUGAR_RESIDENCIA",
      "PROPIEDAD_VIVIENDA",
      "NOMBRE_COLEGIO",
      "DIRECCION_COLEGIO",
      "COD_DEPARTAMENTO_COLEGIO",
      "DEPARTAMENTO_COLEGIO",
      "COD_MUNICIPIO_COLEGIO",
      "MUNICIPIO_COLEGIO",
      "ANO_TERMINACION_COLEGIO",
    "VALOR_MATRICULA",
      "VLR_PAGADO",
      "PERIODO_RECIBO",
      "EPS",
      "RH",
      "DIRECCION_PROCEDENCIA",
      "TEL_PROCEDENCIA",
      "DIRECCION_RESIDENCIA",
      "TEL_RESIDENCIA",
      "LOGIN"
  ]
  # Quitar columnas:
  df_mat_per_v2 = df_mat_per.drop(columns=cols_drop)
  # Crear la columna ID en matriculados:
  df_mat_per_v2["ID"] = df_mat_per_v2["COD_PLAN"].astype(str) + "-" + df_mat_per_v2["DOCUMENTO"].astype(str)
  
  return df_planes, df_activos_discap, df_pav_pap_v2, df_mat_per_v2



"""

def preprocessing_sede(df_planes=None, df_activos=None, df_pav_pap=None, df_mat_per=None):
    if df_planes is None:
        df_planes = ""
    else:
        df_planes['NOMID1'] = df_planes['NOMID1'].apply(unidecode)
        df_planes['NOMID1'] = df_planes['NOMID1'].str.strip()
        df_planes['NOMID1'] = df_planes['NOMID1'].str.upper()

    if df_activos is None:
        df_activos_discap = ""
    else:
        df_activos["ID"] = df_activos["COD_PLAN"].astype(str) + "-" + df_activos["DOCUMENTO"].astype(str)
        df_activos_discap = df_activos[["ID", "DISCAPACIDAD"]]

    if df_pav_pap is None:
        df_pav_pap_v2 = ""
    else:
        df_pav_pap_v2 = df_pav_pap[["COD_PLAN", "DOCUMENTO", "AVANCE_CARRERA"]]
        df_pav_pap_v2["ID"] = df_pav_pap_v2["COD_PLAN"].astype(str) + "-" + df_pav_pap_v2["DOCUMENTO"].astype(str)

    if df_mat_per is None:
        df_mat_per_v2 = ""
    else:
        cols_drop = [
            "FECHA_CARGA_PREINSCRIPCION", "CARNET_UN", "NUMERO_HIJOS", "INGRESOS_FAMILIARES", "PENSION_COLEGIO",
            "CARACTER_COLEGIO", "ESTRATO_VIVIENDA", "LUGAR_RESIDENCIA", "PROPIEDAD_VIVIENDA", "NOMBRE_COLEGIO",
            "DIRECCION_COLEGIO", "COD_DEPARTAMENTO_COLEGIO", "DEPARTAMENTO_COLEGIO", "COD_MUNICIPIO_COLEGIO",
            "MUNICIPIO_COLEGIO", "ANO_TERMINACION_COLEGIO", "VALOR_MATRICULA", "VLR_PAGADO", "PERIODO_RECIBO",
            "EPS", "RH", "DIRECCION_PROCEDENCIA", "TEL_PROCEDENCIA", "DIRECCION_RESIDENCIA", "TEL_RESIDENCIA", "LOGIN"
        ]
        df_mat_per_v2 = df_mat_per.drop(columns=cols_drop)
        df_mat_per_v2["ID"] = df_mat_per_v2["COD_PLAN"].astype(str) + "-" + df_mat_per_v2["DOCUMENTO"].astype(str)

    return df_planes, df_activos_discap, df_pav_pap_v2, df_mat_per_v2



def main_matriculados(df_pav_pap_v2, df_mat_per_v2, df_planes, df_activos_discap, col_out_main, periodo = "2024-1S"):
  # Quitar COD_PLAN y DOCUMENTO ya que esta información esta en ID:
  df_pav_pap_v2 = df_pav_pap_v2.drop(columns=['COD_PLAN','DOCUMENTO'])
  df_mat_per_v2 = df_mat_per_v2.drop(columns=['COD_PLAN','DOCUMENTO'])

  # Guardar las dos df: df_pav_pap_v2, df_mat_per_v2
  data_frames = [df_pav_pap_v2,
                df_mat_per_v2]

  # Hacer un merge del tipo outer entre las dos df por ID (key),
  # y llegar los NaN values mediante espacio vacio de texto:""
  df_merged = reduce(lambda  left,right: pd.merge(left,right,on=['ID'],
                                              how='outer'), data_frames).fillna('')

  # Crear un campo con el ID hasheado:
  df_merged['hashed_ID'] = df_merged['ID'].apply(hash_column)

  # Convertir fecha de nacimiento a string:
  # Para subirlo a google sheets es necesario
  df_merged['FECHA_NACIMIENTO']=df_merged['FECHA_NACIMIENTO'].astype(str)

  # Crear NIVEL_2
  df_merged = set_level_2(df_merged, df_planes)

  # Actualizar merge con discapacidad:
  df_merged = pd.merge(df_merged, df_activos_discap, how = 'left', on='ID')
  # En caso de exitir nan poner desconocida
  df_merged["DISCAPACIDAD"] = df_merged["DISCAPACIDAD"].fillna('desconocida')
  # Cambiar NO y desconocida por SIN DISCAPACIDAD
  df_merged["DISCAPACIDAD"] = df_merged["DISCAPACIDAD"].map(
              {   "NO":"SIN DISCAPACIDAD",
                  "desconocida": "SIN DISCAPACIDAD"}
                              ).fillna(df_merged["DISCAPACIDAD"])

  # Crear rangos (histograma de avance):
  df_merged = crear_avance(df_merged)

  # Cambiar el nombre PAPA_PERIODO a PAPA:
  df_merged.rename(columns={'PAPA_PERIODO': 'PAPA'}, inplace=True)

  # Quitar filas en las cuales la FACULTAD sea Null:
  df_merged = df_merged[df_merged["FACULTAD"]!=""]

  # Cambiar el nombre GENERO a SEXO:
  df_merged.rename(columns={'GENERO': 'SEXO'}, inplace=True)

  # Agregar el periodo del reporte:
  #periodo = "2024-1S"
  df_merged['PERIODO_REPORTE'] = periodo

  # Lista de columnas minimas necesarias:
  cols_main = ["AVANCE_CARRERA",
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

  # Seleccionar las columnas de reporte original:
  df_merged = df_merged[col_out_main]
  # Seleccionar las minimas necesarias para actualizar la base de datos:
  df_merged = df_merged[cols_main]

  # Llenar datos NaN con espacio vacio "":
  df_merged = df_merged.fillna("")
  
  return df_merged


def main_bloq_admin(df_est_bloq, df_activos, df_planes, col_out_hoja_2, periodo="2024-1S"):
  # Crear ID en base de datos de bloqueados:
  df_est_bloq_v2 = df_est_bloq.copy()

  # Cambiar el nombre PAPA_PERIODO a PAPA:
  df_est_bloq_v2.rename(columns={'PAPA_ACTUAL': 'PAPA'}, inplace=True)

  # Cambiar el nombre PBM_CALCULADO a PBM (en Activos):
  df_activos.rename(columns={'PBM_CALCULADO': 'PBM'}, inplace=True)

  # Crear ID en base de datos actuvos y bloqeuados:
  df_est_bloq_v2["DOCUMENTO"] = df_est_bloq_v2["DOCUMENTO"].astype(str)
  df_activos["DOCUMENTO"] = df_activos["DOCUMENTO"].astype(str)
  df_est_bloq_v2["ID"] = df_est_bloq_v2["COD_PLAN"].astype(str) + "-" + df_est_bloq_v2["DOCUMENTO"].astype(str)
  df_activos["ID"] = df_activos["COD_PLAN"].astype(str) + "-" + df_activos["DOCUMENTO"].astype(str)


  # Detectar columnas de bloqueados que estan en base de datos de activos.
  # Con el fin de quitarlas de activos ya que al hacer merge con outer product
  # Habria redundancia en la información.
  col_bloq = list(df_est_bloq_v2.columns)
  col_activos = list(df_activos.columns)
  drop_bloqueados = []
  for col in col_bloq:
      if col in col_activos and col != "ID":
          # guardar en una lista las columnas que se repiten:
          drop_bloqueados.append(col)

  # Borrar de bloqueados las cols que ya estan en activos:
  df_activos_bloq = df_activos.drop(columns=drop_bloqueados)

  # Hacer mergue left entre bloqueados y activos:
  df_bloq_main = pd.merge(df_est_bloq_v2, df_activos_bloq, how='left',on='ID').fillna('')

  # Buscar todas las columnas de tipo Datetime y convertirlas a string
  dates_in_df = list(df_bloq_main.select_dtypes(include=['datetime64']).columns)
  for c_dates in dates_in_df:
      df_bloq_main[c_dates] = df_bloq_main[c_dates].astype(str)

  # Crear ID con hash
  df_bloq_main['hashed_ID'] = df_bloq_main['ID'].apply(hash_column)

  # Crear nivel 2:
  df_bloq_main = set_level_2(df_bloq_main, df_planes)

  # Quitar doble_titulaciones:
  df_bloq_main = df_bloq_main[df_bloq_main['BLOQUEO'] != 'Plan en Doble Titulación']

  # poner desconocidos en DISCAPACIDAD
  df_bloq_main["DISCAPACIDAD"] = df_bloq_main["DISCAPACIDAD"].fillna('desconocida')
  df_bloq_main["DISCAPACIDAD"] = df_bloq_main["DISCAPACIDAD"].map(
      {"NO":"SIN DISCAPACIDAD",
      "desconocida": "SIN DISCAPACIDAD"}
  ).fillna(df_bloq_main["DISCAPACIDAD"])

  # cambiar nombres de columnas:
  df_bloq_main.rename(columns={'PBM_CALCULADO': 'PBM'}, inplace=True)
  df_bloq_main.rename(columns={'GENERO': 'SEXO'}, inplace=True)

  # Crear rangos de avance (histograma):
  df_bloq_main = crear_avance(df_bloq_main)

  # crear periodo de reporte:
  #periodo = "2024-1S"
  df_bloq_main['PERIODO_REPORTE'] = periodo

  # fill con valores nan:
  df_bloq_main = df_bloq_main.fillna("")

  # crear una copia de base de datos de bloqueados:
  df_bloq_main_save = df_bloq_main.copy()

  # Buscar si alguna columna de la lista <col_out_hoja_2> no está
  # en el df de <df_bloq_main_save> y sino está crearla con valores vacios:
  for cols_obj in col_out_hoja_2:
      if cols_obj not in list(df_bloq_main_save.columns):
          df_bloq_main_save[cols_obj] = ""

  # Lista de columnas minimas necesarias:
  col_2_out = ["BLOQUEO",
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
  # Seleccionar las columnas de reporte 2022:
  df_bloq_main_save = df_bloq_main_save[col_out_hoja_2]
  # Luego, seleccionar de estas las minimas necesarias:
  df_bloq_main_save = df_bloq_main_save[col_2_out]

  return df_bloq_main_save


def main_bloq_academ(df_pav_pap, df_matriculados_ant, df_planes, df_activos_discap, df_mat_per_v2, col_out_hoja_3, periodo = "2024-1S"):
  # df_pav_pap.info()
  df_matr_avc = df_pav_pap.copy()


  # crear ID en matriculados con avance:
  df_matr_avc["ID"] = df_matr_avc["COD_PLAN"].astype(str) + "-" + df_matr_avc["DOCUMENTO"].astype(str)
  # seleccionar ID y avance de carrera unicamente:
  df_matr_avc = df_matr_avc[["ID","AVANCE_CARRERA"]]

  # crear ID en estudiantes matriculados:
  df_matriculados_ant["ID"] = df_matriculados_ant["COD_PLAN"].astype(str) + "-" + df_matriculados_ant["DOCUMENTO"].astype(str)

  # Seleccionar todos los bloqueados cuyo campo no esté vacio.
  # llenar los nana con "":
  df_matriculados_ant["BLOQUEO"] = df_matriculados_ant["BLOQUEO"].fillna("")
  # Seleccionar los casos en los cuales el len del str es distinto que 0:
  df_matriculados_ant_bloq =  df_matriculados_ant[df_matriculados_ant["BLOQUEO"].str.len() != 0]

  # Agregar avance por ID:
  df_bloq_avc = df_matriculados_ant_bloq.merge(df_matr_avc, on='ID', how="left")

  # Cambiar todas las fechas de datetime a str:
  dates_in_df = list(df_bloq_avc.select_dtypes(include=['datetime64']).columns)
  for c_dates in dates_in_df:
      df_bloq_avc[c_dates] = df_bloq_avc[c_dates].astype(str)

  # Rellenar con Nan:
  df_bloq_avc = df_bloq_avc.fillna("")

  # poner ID hasheado:
  df_bloq_avc['hashed_ID'] = df_bloq_avc['ID'].apply(hash_column)

  # Poner Nivel 2:
  df_bloq_avc = set_level_2(df_bloq_avc, df_planes)

  # Se agrega la discapacidad con activos:
  # Actualizar merge con discapacidad:
  df_merged = pd.merge(df_bloq_avc, df_activos_discap, how = 'left', on='ID')
  # En caso de exitir nan poner desconocida
  df_merged["DISCAPACIDAD"] = df_merged["DISCAPACIDAD"].fillna('desconocida')
  df_merged["DISCAPACIDAD"] = df_merged["DISCAPACIDAD"].map(
      {"NO":"SIN DISCAPACIDAD",
      "desconocida": "SIN DISCAPACIDAD"}
  ).fillna(df_merged["DISCAPACIDAD"])


  # llenar datos vacios en bloque:
  df_merged["BLOQUEO"] = df_merged["BLOQUEO"].fillna("")
  # resumir causa de bloqueo:
  df_merged["CAUSA_BLOQUEO"] = df_merged["BLOQUEO"].apply(causa_bloq)

  # Renombrar columnas:
  df_merged.rename(columns={'PAPA_PERIODO': 'PAPA'}, inplace=True)
  df_merged.rename(columns={'GENERO': 'SEXO'}, inplace=True)

  # Seleccionar de matriculados unicamente ID, EDAD y PBM:
  if "EDAD" not in df_merged.columns:
    df_mat_per_v2_b = df_mat_per_v2[["ID","EDAD"]]
    data_frames = [df_merged,
                  df_mat_per_v2_b]
    # Hacer merge con left entre base de datos df_merged y df_mat_per_v2_b:
    df_merged = reduce(lambda  left,right: pd.merge(left,right,on=['ID'],
                                                how='left'), data_frames).fillna('')
  if "PBM" not in df_merged.columns:
    df_mat_per_v2_b = df_mat_per_v2[["ID","PBM"]]
    data_frames = [df_merged,
                  df_mat_per_v2_b]
    # Hacer merge con left entre base de datos df_merged y df_mat_per_v2_b:
    df_merged = reduce(lambda  left,right: pd.merge(left,right,on=['ID'],
                                                how='left'), data_frames).fillna('')

  print("===================SALIDA DE MATRICULADOS DE II df_merged> : ")
  print(df_merged.info())
  
  # Hacer lista con las columnas necesarias en funcion de las columnas
  # del mismo reporte del 2022:
  col_out_hoja_3_b = []
  for c in col_out_hoja_3:
      if c == "GENERO":
          c = "SEXO"
      col_out_hoja_3_b.append(c)
  #col_out_hoja_3_b.append("EDAD")
  #col_out_hoja_3_b.append("PBM")

  # Crear rangos de avance (histograma):
  df_merged = crear_avance(df_merged)

  # agregar periodo:
  # periodo = "2024-1S"
  df_merged['PERIODO_REPORTE'] = periodo

  # Seleccionar las columnas necesarias:
  df_merged = df_merged[col_out_hoja_3_b]
  
  if "PAPA_ACTUAL" in df_merged.columns:
    df_merged.rename(columns={"PAPA_ACTUAL": "PAPA"}, inplace=True)
  
  return  df_merged


# =================== CHECK MAIN =======================


def check_repeat_main(df_historico, cols_gsh):
  """
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
  """
  
  #resultado = df_historico
  print("Numero de filas:")
  print(len(df_historico))

  # Seleccionar filas no duplicadas:
  filas_no_duplicadas = df_historico[~df_historico.duplicated(keep=False)]

  # Seleccionar filas duplicadas:
  filas_duplicadas = df_historico[df_historico.duplicated(keep=False)]

  print("Filas duplicadas:")
  print(len(filas_duplicadas))

  # Quitar duplicadas por ID y periodo:
  df_nuevo = filas_duplicadas.drop_duplicates(subset=['ID', 'PERIODO_REPORTE'])

  print("df sin filas duplicadas:")
  print(len(df_nuevo))

  # Concatenar datos no duplicados con datos recuperados:
  df_final = pd.concat([filas_no_duplicadas, df_nuevo])

  print("df final:")
  print(len(df_final))
  
  # check columnas:
  df_main = df_final[cols_gsh]
  
  return df_main

def format_column(df, column_name, option):
    """
    Formatea una columna específica de un DataFrame según la opción seleccionada.

    Parámetros:
    - df: DataFrame de entrada.
    - column_name: Nombre de la columna a formatear.
    - option: "to_int" para formatear como enteros sin ".0" o "to_float" para formatear como flotantes con coma.

    Retorna:
    - DataFrame con la columna formateada.
    """
    try:
      if option == "to_int":
          # Convertir a float, luego a int para eliminar la parte decimal, y finalmente a string
          df[column_name] = df[column_name].apply(
              lambda x: str(int(float(x))) if x != '' and pd.notnull(x) else ''
          )
      elif option == "to_float":
          
          df[column_name] = df[column_name].apply(
              lambda x: "{:,.2f}".format(float(x)).replace('.', ',') if x != '' and pd.notnull(x) else ''
          )
      else:
          raise ValueError("La opción debe ser 'to_int' o 'to_float'")
      return df
    except:
      return df