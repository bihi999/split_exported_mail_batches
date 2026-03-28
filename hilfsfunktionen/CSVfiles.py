
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