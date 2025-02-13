import os
import json
import pandas as pd

class ExcelFileChecker:
    def __init__(self, folder_path, config, id_):
        """
        :param folder_path: Ruta de la carpeta donde se encuentran los archivos .xlsx
        :param config: Configuración cargada desde el archivo JSON
        :param id_: ID para obtener la configuración específica de ese conjunto
        """
        self.folder_path = folder_path
        self.expected_sheets = config[id_]["expected_sheets"]
        self.expected_columns = config[id_]["expected_columns"]

    def _list_xlsx_files(self):
        """Lista todos los archivos .xlsx en la carpeta especificada."""
        return [f for f in os.listdir(self.folder_path) if f.endswith('.xlsx')]

    def check_files_exist(self):
        """Verifica si todos los archivos esperados están en la carpeta."""
        xlsx_files = self._list_xlsx_files()
        missing_files = [f for f in self.expected_sheets if f not in xlsx_files]
        return missing_files == [], missing_files

    def check_sheet_names(self):
        """Verifica si cada archivo tiene las hojas esperadas."""
        missing_sheets = {}
        for file_name, sheets in self.expected_sheets.items():
            file_path = os.path.join(self.folder_path, file_name)
            try:
                xls = pd.ExcelFile(file_path)
                actual_sheets = xls.sheet_names
                for sheet in sheets:
                    if sheet not in actual_sheets:
                        missing_sheets.setdefault(file_name, []).append(sheet)
            except FileNotFoundError:
                missing_sheets[file_name] = sheets
        return missing_sheets == {}, missing_sheets

    def check_columns_in_sheet(self):
        """Verifica si cada hoja tiene las columnas esperadas."""
        missing_columns = {}
        for file_name, sheet_columns in self.expected_columns.items():
            file_path = os.path.join(self.folder_path, file_name)
            try:
                for sheet_name, columns in sheet_columns.items():
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
                    actual_columns = df.columns.tolist()
                    for column in columns:
                        if column not in actual_columns:
                            missing_columns.setdefault((file_name, sheet_name), []).append(column)
            except FileNotFoundError:
                missing_columns[(file_name, sheet_name)] = columns
            except ValueError:
                missing_columns[(file_name, sheet_name)] = columns
        return missing_columns == {}, missing_columns

    def run_all_checks(self):
        """Ejecuta todas las verificaciones y retorna un resumen."""
        file_check, missing_files = self.check_files_exist()
        sheet_check, missing_sheets = self.check_sheet_names()
        column_check, missing_columns = self.check_columns_in_sheet()

        summary = {
            "files_check": file_check,
            "missing_files": missing_files,
            "sheets_check": sheet_check,
            "missing_sheets": missing_sheets,
            "columns_check": column_check,
            "missing_columns": missing_columns
        }
        return summary