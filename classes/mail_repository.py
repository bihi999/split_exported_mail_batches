from dataclasses import fields, is_dataclass
from typing import Any, Dict, List, Tuple

import pandas as pd

from classes.mail_model import Mail


class DictForMail:
    """
    Repository-Klasse für Mail-Objekte.

    Attribute:
        _items (Dict[int, Mail]):
            Dictionary mit Mail-ID als Schlüssel und Mail-Instanzen als Werte.

        raw_data (List[Tuple[str, str, str]]):
            Liste von Tupeln/Listen (absender, betreff, text)

        absender (set[str]):
            Menge aller bereits verarbeiteten Absender (zur Deduplizierung)
    """

    def __init__(self, raw_data: List[Tuple[str, str, str]] = None):
        """
        Initialisiert das Repository.

        :param raw_data: Liste von 3er-Tupeln (absender, betreff, text)
        """
        self._items: Dict[int, Mail] = {}
        self.raw_data = raw_data or []
        self.absender: set[str] = set()

    def add(self, obj: Mail) -> None:
        """
        Fügt eine Mail-Instanz hinzu (Key = Mail-ID).

        :param obj: Mail-Objekt
        """
        self._items[obj.id] = obj
        self.absender.add(obj.absender)

    @staticmethod
    def from_raw_data(raw_data: Any, logger) -> "DictForMail":
        """
        Erstellt ein DictForMail-Objekt aus Rohdaten.
        Validiert die Struktur und erzeugt Mail-Instanzen.

        :param raw_data: Liste von 3er-Tupeln/Listen [(absender, betreff, text), ...]
        :return: Instanz von DictForMail
        :raises ValueError: bei ungültiger Struktur oder ungültiger E-Mail
        """

        if not isinstance(raw_data, list):
            raise ValueError("raw_data muss eine Liste sein")

        # Regex aus Mail-Klasse verwenden
        email_pattern = Mail.DEFAULT_EMAIL_PATTERN

        repo = DictForMail(raw_data=raw_data)

        logger.info(f"................................................................................................")
        logger.info(f"DictForMail.from_raw_data: Starte Verarbeitung on Liste mit Rohdaten der Länge {len(raw_data)}")

        defect_row_counter = {"KeineListe": 0,
                              "NichtAlleStrings": 0,
                              "KeineEMailAdresse": 0,
                              "InstanziierungFehlgeschlagen": 0} # Keine Liste, Nicht alles Strings, absender keine E-Mail-Adresse, Instanziierung geht fehl

        for entry in raw_data:
            if not isinstance(entry, (list, tuple)) or len(entry) != 3:
                logger.info(f"DictForMail.from_raw_data: Jeder Eintrag muss 3er-Tupel oder Liste sein (absender, betreff, text) - erhalten Typ {type(entry)} mit Länge {len(entry)}")
                defect_row_counter["KeineListe"] += 1
                continue
            absender, betreff, text = entry

            # --- Typprüfung ---
            if not all(isinstance(x, str) for x in entry):
                defect_row_counter['NichtAlleStrings'] += 1
                logger.info(f"DictForMail.from_raw_data: Nicht jeder Eintrag in Liste / Tupel ist ein String.")
                continue

            # --- Validierung absender (E-Mail-Pattern) ---
            if not email_pattern.search(absender):
                defect_row_counter['KeineEMailAdresse'] += 1
                logger.info(f"DictForMail.from_raw_data: Ausgelesener absender entspricht nicht dem Mail-Pattern.")
                continue

            # --- Instanziierung ---
            try:
                mail = Mail(absender, betreff, text)
            except:
                defect_row_counter["InstanziierungFehlgeschlagen"] += 1
                logger.info(f"DictForMail.from_raw_data: Instanziierung von Mail-Objekt aus Tupel fehlgeschlagen")
                continue

            repo.add(mail)

        frd_counter1 = 0
        for key in defect_row_counter.keys():
            logger.info(f"DictForMail.from_raw_data: Für {defect_row_counter[key]} - Fälle den Fehler {key} erhalten.")
            frd_counter1 += defect_row_counter[key]
        logger.info(f"DictForMail.from_raw_data: {(frd_counter1/len(raw_data))*100:.2f} Fehlerquote.")

        return repo

    def deduplizieren(self) -> "DictForMail":
        """
        Erstellt eine neue DictForMail-Instanz ohne fachlich doppelte Mail-Objekte.

        Die Gleichheit der Mail-Objekte wird über Mail.__eq__ und Mail.__hash__
        definiert.
        """
        repo = DictForMail(raw_data=self.raw_data)
        bekannte_mails: set[Mail] = set()

        for mail in self._items.values():
            if mail in bekannte_mails:
                continue

            bekannte_mails.add(mail)
            repo.add(mail)

        return repo

    def print_thematische_zuordnungen(self) -> None:
        """
        Gibt alle thematischen Zuordnungen aller Mails aus.
        """
        for mail in self._items.values():
            print(f"Absender: {mail.absender}, Betreff: {mail.betreff}")
            for thema, schlagwortliste, satz in mail.thematische_zuordnungen:
                print(f"Thema: {thema}")
                print(f"Schlagworte: {', '.join(schlagwortliste)}")
                print(f"Satz: {satz}")
                print("-" * 40)
            print("=" * 40)

    def export_thematische_zuordnungen_to_excel(self, export_folder: str) -> None:
        """
        Exportiert thematische Zuordnungen in eine Excel-Datei.

        :param export_folder: Zielordner
        """
        data = []

        for mail in self._items.values():
            for thema, schlagwortliste, satz in mail.thematische_zuordnungen:
                data.append([
                    mail.absender,
                    thema,
                    " ".join(schlagwortliste),
                    satz.replace('\n', ' ').replace('\r', '').replace('\t', '')
                ])

        df = pd.DataFrame(
            data,
            columns=['absender', 'thema', 'schlagworte', 'satz']
        )

        df.to_excel(f"{export_folder}/thematische_zuordnungen.xlsx", index=False)

    def export_raw_mails_to_excel(self, export_path: str, logger, deduplicate_mode = "none") -> None:
        """
            Export aller Mailinstanzen mit ihren Attributen in eine Exceltabelle.
            Mails können nach Absender und Textinhalt dedupliziert werden.
            Umsetzung durch variablen Dict-Schlüssel je nach gewünschter Deduplizierungs-Art.

        """
        import uuid #Universally Unique Identifier
        from pathlib import Path
        
        export_dict = {}

        def make_key(mail_sender, mail_text, deduplicate_mode):
            if deduplicate_mode == "none":
                return uuid.uuid4()
            elif deduplicate_mode == "sender":
                return mail_sender
            elif deduplicate_mode == "sender_text":
                return (mail_sender, mail_text)
            else:
                raise ValueError(f"Dict.ForMail.export_raw_mails_to_excel: Unbekannter Wert für deduplicate_mode: {deduplicate_mode}")
        
    
        for item in self._items.values():
            sender = item.absender
            text = item.text
            topic = item.betreff
            dict_key = make_key(sender, text, deduplicate_mode)

            if dict_key in export_dict.keys():
                continue
            else:
                export_dict[dict_key] = { "absender" : sender,
                                          "betreff" : topic,
                                          "text" : text}
        
        df = pd.DataFrame.from_dict(export_dict, orient="index")
        
        ordner = export_path
        file = "rohdaten"
        suffix = deduplicate_mode
        
        export_path_completed = Path(ordner) / f"{file}{suffix}.xlsx"
        
        df.to_excel(export_path_completed, index=False)
    
    
    
    def export_mails_to_excel(self, export_path: str) -> None:
        """
        Generischer Export:
        - verarbeitet ausschließlich Dataclass-Instanzen in mail.matches
        - jede Instanz = eine Zeile
        - alle Attribute werden exportiert (auch None)
        - nicht-Dataclass-Objekte → eine Fehlerzeile
        """

        themen_dict = {}
        mails_ohne_thema = []

        # Themen werden aus thematische_zuordnungen abgeleitet.
        for mail in self._items.values():
            themen = [thema for thema, _, _ in mail.thematische_zuordnungen]

            if not themen:
                mails_ohne_thema.append(mail)

            for thema in themen:
                if thema not in themen_dict:
                    themen_dict[thema] = []
                themen_dict[thema].append(mail)

        def _clean_text(text: str) -> str:
            return text.replace("\n", " ").replace(",", "").replace(";", "")

        def _process_match(match) -> dict:
            """
            Wandelt ein Match-Objekt in ein Dictionary um.
            """

            # Dataclass prüfen
            if is_dataclass(match) and not isinstance(match, type):
                try:
                    data = {
                        field.name: getattr(match, field.name)
                        for field in fields(match)
                    }
                    data["__class__"] = match.__class__.__name__
                    return data

                except Exception as e:
                    return {
                        "__class__": match.__class__.__name__,
                        "__error__": f"Fehler beim Auslesen: {e}"
                    }

            # Fallback für Nicht-Dataclasses
            return {
                "__class__": match.__class__.__name__,
                "__error__": "Kein Dataclass-Objekt"
            }

        def _build_rows_for_mail(mail):
            """
            Erzeugt alle Zeilen für eine Mail.
            """
            base_data = {
                "absender": mail.absender,
                "betreff": mail.betreff,
                "text": _clean_text(mail.text)
            }

            rows = []

            matches = getattr(mail, "matches", set())

            if not matches:
                # eine leere Zeile ohne Match-Daten
                rows.append(base_data.copy())
                return rows

            for match in matches:
                match_data = _process_match(match)

                row = base_data.copy()
                row.update(match_data)

                rows.append(row)

            return rows

        def _export_block(mails_list, filename):
            data = []

            for mail in mails_list:
                data.extend(_build_rows_for_mail(mail))

            df = pd.DataFrame(data)
            df.to_excel(f"{export_path}/{filename}.xlsx", index=False)

        # Export je Thema
        for thema, mails_list in themen_dict.items():
            _export_block(mails_list, thema)

        # Export ohne Thema
        if mails_ohne_thema:
            _export_block(mails_ohne_thema, "ohne_thema")

    def export_references_to_excel(self, export_path: str, logger, show_dataframe: bool = False):
        """
            Erstelle eine leere Liste.
            Iteriere über die Mail-Instanzen in self._items und calle referenzen_umgebung_ausgeben.
            Sammle die in Listen organisierten Dictionaries in der erzeugten Liste.
            Erzeuge daraus einen Data Frame.
            Schreibe ihn via .to_excel in den export_path.

            Args:   counter_keine_referenzen (int) - Zähler wieviele Mail - Instanzen keine Referenzen enthalten
                    counter_verlorene_referenzen (int) - Zähler wieviele Mail -Instanzen Referenzen haben Referenzen aber sie unvollständig oder gar nicht zurückgeben
        """

        logger.info(f"export_references_to_excel: Start Zusammenfassung der Referenzen und ihrer Fundstellen.")
        counter_keine_referenzen = 0
        counter_verlorene_referenzen = 0
        
        liste_ermittelter_referenzen = []
        for mail in self._items.values():
            if mail.referenzen:
                ermittelte_referenzen = mail.referenzen_umgebung_ausgeben(logger)
                if any(referenz.get("text") is None for referenz in ermittelte_referenzen):
                    counter_verlorene_referenzen += 1
                elif len(ermittelte_referenzen) < len(mail.referenzen):
                    counter_verlorene_referenzen += 1
                
                liste_ermittelter_referenzen.extend(ermittelte_referenzen) # Reminder: Einzelelemente werden hinzugefügt. Keine Deduplizierung.
            
            else:
                counter_keine_referenzen += 1

        logger.info(f"export_references_to_excel: {len(self._items)} Mail-Instanzen - {counter_keine_referenzen} ohne Referenzen - {counter_verlorene_referenzen} verlorene Referenzen - {len(liste_ermittelter_referenzen)} unique Referenzen.")

        referenzen_dict_gekuerzt = pd.DataFrame(liste_ermittelter_referenzen)
        if show_dataframe:
            print(referenzen_dict_gekuerzt.head())
        referenzen_dict_gekuerzt.to_excel(export_path, index=False)
