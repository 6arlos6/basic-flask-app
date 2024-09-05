from types import MappingProxyType

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
my_config_constants = Constantes( type_gsheet_write_sede = "servicio",
                                  name_file_gsheet_sede = "UIA-FACULTADES_V2",
                                  type_gsheet_write_dates = "servicio",
                                  name_file_gsheet_dates = 'UIA-Historial_dates')