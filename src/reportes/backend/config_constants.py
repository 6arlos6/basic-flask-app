from types import MappingProxyType
import os

class Constantes:
    def __init__(self, **kwargs):
        # Crear un diccionario con las constantes proporcionadas
        self._constantes = MappingProxyType(kwargs)

    @property
    def constantes(self):
        # Devuelve el diccionario inmutable
        return self._constantes

    def __getitem__(self, key):
        # Permite acceder a las constantes como si fuera un diccionario
        return self._constantes[key]

    def __repr__(self):
        # Representación de la clase para facilitar la depuración
        return f"Constantes({dict(self._constantes)})"
    
# Ejemplo de uso

my_config_constants_local = Constantes( type_gsheet_write_sede = "servicio",
                                  name_file_gsheet_sede = "UIA-FACULTADES_V2",
                                  type_gsheet_write_dates = "servicio",
                                  name_file_gsheet_dates = 'UIA-Historial_dates',
                                  mysql_username = "root",
                                  mysql_host = "localhost",
                                  mysql_password = "",
                                  mysql_db = "flask_login",
                                  upload_folder = os.path.join("src","data"),
                                  flask_secret_key = "B!1w8NAt1T^%kvhUI*S^",
                                  principal_path = os.path.join("src","data"),
                                  path_principal_2 = os.path.join('src','data','static_data', 'sede'),
                                  path_save_sede = os.path.join('src','data','sede','generados'),
                                  path_send_file_1 = os.path.join('src','data',"my_reporte.xlsx"),
                                  path_send_file_2 = os.path.join('src','data',"my_reporte_date.xlsx"),
                                  path_json_google_sheets = os.path.join("src","reportes","security","dama-datos.json"),
                                  # dama servicios
                                  name_file_gsheet_servicios_dama = "UIA-REPORTES_DAMA")


my_config_constants_server = Constantes( type_gsheet_write_sede = "servicio",
                                  name_file_gsheet_sede = "UIA-FACULTADES_V2",
                                  type_gsheet_write_dates = "servicio",
                                  name_file_gsheet_dates = 'UIA-Historial_dates',
                                  mysql_username = "root",
                                  mysql_host = "localhost",
                                  mysql_password = "mySQ|d4m4*",
                                  mysql_db = "flask_login",
                                  upload_folder = os.path.join('home','Analisis','basic-flask-app',"src","data"),
                                  flask_secret_key = "B!1w8NAt1T^%kvhUI*S^",
                                  principal_path = os.path.join('home','Analisis','basic-flask-app',"src","data"),
                                  path_principal_2 = os.path.join('home','Analisis','basic-flask-app','src','data','static_data', 'sede'),
                                  path_save_sede = os.path.join('home','Analisis','basic-flask-app','src','data','sede','generados'),
                                  path_send_file_1 = os.path.join('home','Analisis','basic-flask-app','src','data',"my_reporte.xlsx"),
                                  path_send_file_2 = os.path.join('home','Analisis','basic-flask-app','src','data',"my_reporte_date.xlsx"),
                                  path_json_google_sheets = os.path.join('home','Analisis',"json_key_google_sheets","dama-datos.json"))

my_config = {
    "local":my_config_constants_local,
    "server":my_config_constants_server
}

# Configuraciones
my_config_constants = my_config["local"]