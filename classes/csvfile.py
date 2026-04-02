
from typing import List, Dict, Set
from io import StringIO
from dataclasses import dataclass
import os
import pandas as pd
from collections import Counter

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]


class CSVHandler:
    def __init__(self, filepath: str, encoding: str = "utf-8", content: str = ""):
        self.filepath = filepath
        self.encoding = encoding
        self.content = content  # neues Attribut
        self.exceptions = set() # neues Attribut

    @staticmethod
    def validate_file(filepath: str, expected_encoding: str = "utf-8") -> ValidationResult:
        errors = []

        dir_path = os.path.dirname(filepath) or "."

        if not os.path.exists(dir_path):
            errors.append("DIRECTORY_NOT_FOUND")

        elif not os.access(dir_path, os.R_OK):
            errors.append("DIRECTORY_NOT_READABLE")

        elif not os.path.exists(filepath):
            errors.append("FILE_NOT_FOUND")

        elif not os.path.isfile(filepath):
            errors.append("NOT_A_FILE")

        else:
            if not filepath.lower().endswith(".csv"):
                errors.append("INVALID_TYPE")

            if os.path.getsize(filepath) == 0:
                errors.append("EMPTY_FILE")

            if not errors:
                try:
                    with open(filepath, "r", encoding=expected_encoding) as f:
                        f.read(1024)
                except UnicodeDecodeError:
                    errors.append("ENCODING_ERROR")
                except Exception:
                    errors.append("UNKNOWN_ERROR")

        return ValidationResult(len(errors) == 0, errors)

    @classmethod
    def from_file(cls, filepath: str, encoding: str = "utf-8"):
        # Encoding wird hier weitergereicht → gleiche Prüfung
        result = cls.validate_file(filepath, encoding)

        if not result.is_valid:
            print(f"[VALIDATION FAILED] {result.errors}")
            return None

        # Datei vollständig einlesen
        with open(filepath, "r", encoding=encoding) as f:
            content = f.read()

        return cls(filepath, encoding, content)
    

    def csv_to_pandas(self, sep):
        """
        Keine Dopplung - verarbeitet wird der bereits eingelesene
        Content - wird dafür gepuffert. Keine Redundanz - der DF
        soll nicht dauerhaft gespeichert - nur weitergereicht werden.
        
        Liest self.content in einen pandas DataFrame.
        - Kein Default für sep
        - Bei Fehler: Exception-Typ zurückgeben + Exception speichern
        """
        try:
            df = pd.read_csv(
                StringIO(self.content),
                sep=sep,
                encoding=self.encoding,
                engine="python"  # wichtig für flexible Separatoren
            )
            return df

        except Exception as e:
            self.exceptions.add(e)
            return type(e)
   
    
    def transform_pandas(self, df, mapping: dict, use_case: str):
        """
        Transformiert einen DataFrame basierend auf einem Mapping.

        - mapping: Dict mit Use-Cases
        - use_case: z. B. "abgleich_dwh"
        - Rückgabe:
            - DataFrame bei Erfolg
            - Exception-Typ bei Fehler
        """

        try:
            if use_case not in mapping:
                raise KeyError(f"Use case '{use_case}' nicht im Mapping vorhanden")

            config = mapping[use_case]

            # Spalten prüfen
            missing_cols = [col for col in config.keys() if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Fehlende Spalten: {missing_cols}")

            # Transformation anwenden
            for col, func in config.items():
                if func is not None:
                    df[col] = func(df[col])

            return df

        except Exception as e:
            self.exceptions.add(e)
            return type(e)


    def split_content(self, separators: list[str]):
        """
        Zerlegt self.content hierarchisch anhand mehrerer Regex-Separatoren.

        Konzept:
        ----------
        Die Zerlegung erfolgt rekursiv / verschachtelt (nested), nicht flach.
        Jeder Separator entspricht einer Hierarchieebene.

        Beispiele:
        ----------
        - ["\\n", "\\|"]  → Mail -> Feld
        - ["\\n", "\\|", "\\."] → Mail -> Feld -> Satz

        Ablauf:
        ----------
        1. Auf oberster Ebene wird der gesamte Inhalt gesplittet
        2. Für jedes Teilstück wird der nächste Separator angewendet
        3. Dies erfolgt rekursiv bis zur letzten Ebene

        Ergebnis:
        ----------
        - Verschachtelte Listenstruktur entsprechend der Hierarchie
        - Report mit Strukturinformationen

        Einschränkungen:
        ----------
        - Maximal 3 Separatoren erlaubt

        Rückgabe:
        ----------
        Tuple:
        (
            nested_structure: list,
            report: dict
        )

        Bei Fehler:
        ----------
        - Exception wird gespeichert
        - Rückgabe: Exception-Typ
        """

        if not separators or len(separators) > 3:
            raise ValueError("Es sind 1 bis maximal 3 Separatoren erlaubt.")

        try:
            level_counts = {}

            def recursive_split(text, seps, level=1):
                parts = re.split(seps[0], text)
                level_counts[f"level_{level}"] = level_counts.get(f"level_{level}", 0) + len(parts)

                if len(seps) == 1:
                    return parts
                else:
                    return [recursive_split(p, seps[1:], level + 1) for p in parts]

            nested = recursive_split(self.content, separators)

            # Analyse der Blattlängen (Endebene)
            def collect_leaf_lengths(data):
                if isinstance(data, list):
                    if all(not isinstance(x, list) for x in data):
                        return [len(data)]
                    else:
                        result = []
                        for item in data:
                            result.extend(collect_leaf_lengths(item))
                        return result
                return []

            leaf_lengths = collect_leaf_lengths(nested)
            tuple_lengths = dict(Counter(leaf_lengths))

            report = {
                "levels": len(separators),
                "separators": separators,
                "level_counts": level_counts,
                "leaf_group_sizes": tuple_lengths,
            }

            return nested, report

        except Exception as e:
            self.exceptions.add(e)
            return type(e)


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

