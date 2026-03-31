
import os
from typing import List, Dict, Set

import os
import os
from dataclasses import dataclass
from typing import List


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]


class CSVHandler:
    def __init__(self, filepath: str, encoding: str = "utf-8"):
        self.filepath = filepath
        self.encoding = encoding

    @staticmethod
    def validate_file(filepath: str, expected_encoding: str = "utf-8") -> ValidationResult:
        
        import os

        dir_path = os.path.dirname(filepath) or "."
        file_name = os.path.basename(filepath)
        
        errors = []

        # Existenz prüfen
        if not os.path.exists(dir_path):
            errors.append("DIRECTORY_NOT_FOUND")

        elif not os.access(dir_path, os.R_OK):
            errors.append("DIRECTORY_NOT_READABLE")

        elif not os.path.exists(filepath):
            errors.append("FILE_NOT_FOUND")

        elif not os.path.isfile(filepath):
            errors.append("NOT_A_FILE")

        else:
            # Lesbarkeit prüfen
            if not os.access(filepath, os.R_OK):
                errors.append("NOT_READABLE")

            # Dateiendung prüfen
            if not filepath.lower().endswith(".csv"):
                errors.append("INVALID_TYPE")

            # Größe prüfen
            if os.path.getsize(filepath) == 0:
                errors.append("EMPTY_FILE")

            # Encoding prüfen (nur wenn bisher sinnvoll)
            if not errors:
                try:
                    with open(filepath, "r", encoding=expected_encoding) as f:
                        f.read(1024)
                except UnicodeDecodeError:
                    errors.append("ENCODING_ERROR")
                except Exception:
                    errors.append("UNKNOWN_ERROR")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    @classmethod
    def from_file(cls, filepath: str, encoding: str = "utf-8"):
        result = cls.validate_file(filepath, encoding)

        if not result.is_valid:
            print(f"[VALIDATION FAILED] {result.errors}")
            return None

        return cls(filepath, encoding)


def read_csv_as_string(file_path: str) -> str:
    """
    Liest eine CSV-Datei ein und gibt deren Inhalt als String zurück.
    
    :param file_path: Pfad zur CSV-Datei
    :return: Inhalt der CSV-Datei als String
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    


def csv_to_dict(filepath: str, delimiter: str = ';', encoding: str = 'utf-8', dublettenloeschung: bool = False) -> Dict[str, Dict[str, Set]]:
    """
    Liest eine CSV-Datei ein und wandelt sie in ein Dictionary um.
    
    :param filepath: Pfad zur CSV-Datei
    :param delimiter: Trenner in der CSV-Datei, Default ist Semikolon
    :param encoding: Encoding der CSV-Datei, Default ist UTF-8
    :param dublettenloeschung: Boolescher Wert, ob Dubletten gelöscht werden sollen, Default ist False
    :return: Dictionary mit den Daten aus der CSV-Datei
    :raises ValueError: Wenn die Spalte 'absender' nicht in der CSV-Datei vorhanden ist
    """
    # Einlesen der CSV-Datei in einen DataFrame
    df = pd.read_csv(filepath, delimiter=delimiter, encoding=encoding)
    
    # Überprüfen, ob die Spalte 'absender' vorhanden ist
    if 'absender' not in df.columns:
        raise ValueError("Die Spalte 'absender' muss in der CSV-Datei vorhanden sein.")
    
    # Konvertieren der Spalten "webfirmenid" und "webid" zu Ganzzahlen
    for col in ['webfirmenid', 'webid']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(pd.NA).astype('Int64')
    
    result_dict = {}
    
    # Iterieren über die Zeilen des DataFrames
    for _, row in df.iterrows():
        absender = row['absender']
        if absender not in result_dict:
            result_dict[absender] = {col: set() if pd.isna(row[col]) else {row[col]} for col in df.columns if col != 'absender'}
        else:
            if not dublettenloeschung:
                for col in df.columns:
                    if col != 'absender':
                        if pd.isna(row[col]):
                            result_dict[absender][col].update()
                        else:
                            result_dict[absender][col].add(row[col])
    
    return result_dict