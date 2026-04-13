import re
from typing import List, Tuple, Dict, Any
import pandas as pd
import pprint
from dataclasses import is_dataclass, fields


class Mail:
    """
    Repräsentiert eine E-Mail mit Absender, Betreff und Text.
    """
    def __init__(self, absender: str, betreff: str, text: str):
        """
        Initialisiert eine Mail-Instanz.
        
        :param absender: Absender der E-Mail
        :param betreff: Betreff der E-Mail
        :param text: Text der E-Mail
        """
        self.absender = absender
        self.betreff = betreff
        self.text = text
        
        self.saetze = []  
        
        #--------       self.deutsche_saetze = [] - Logik unklar - Redundanz und zugleich Nutzen unklar.
        
        self.themen = []  # Wird gleichsinnig zu thematische_zuordnungen befüllt - Wieder: Redundanz

        self.sentimente = set()     # Jede Testfunktion setzt voraus dass der E-Mail von außen bereits ermittelte Sentimente übergeben werden können
        
        #--------       self.kunde = False - Eine Mail hat keine Kundeneigenschaft
        #--------       self.status = "" - Eine Mail hat keinen Aktivitätsstatus
        #--------       self.webid = set() - Eine Mail hat selbst keine direkte Verbindung zu einer WebID
        
        self.thematische_zuordnungen = []  # Treffer werden hier hinterlegt - also die Zuordnung von Text zu einem bestimmten Sentiment - die Tupel-Struktur der Schlagwortmethode muss noch generalisiert werden
        self.referenzen = set()   # Menge zum Speichern von Mailadressen die in der E-Mail erwähnt werden

        self.matches = set()   # Abgleich aus der Mail heraus führen zu Treffer-Objekten die hier gespeichert werden




    def satztrenner(self) -> None:
        """
        Trennt das Attribut 'text' in Sätze auf und speichert sie in der Liste 'saetze'.
        """
        # Regex-Pattern für Satzzeichen, die das Ende eines Satzes markieren
        satzzeichen = re.compile(r'(?<!\d)(?<!\.\d)[.!?](?!\d)(?!\.[a-zA-Z])\s')

        # Trennen des Texts in Sätze
        def split_text(text):
            pos = 0
            saetze = []
            while pos < len(text):
                match = satzzeichen.search(text, pos)
                if not match:
                    saetze.append(text[pos:].strip())
                    break
                end = match.end()
                saetze.append(text[pos:match.start() + 1].strip())  # Ende des Satzes inklusive Satzzeichen
                pos = match.end() - 1  # Start der Suche ab dem Zeichen nach dem Satzzeichen
            return saetze
        
        self.saetze = split_text(self.text)

    @staticmethod
    def is_probably_german(satz: str) -> bool:
        """
        Überprüft, ob ein Satz wahrscheinlich aus der deutschen Sprache stammt.
        
        :param satz: Zu überprüfender Satz
        :return: True, wenn der Satz wahrscheinlich deutsch ist, sonst False
        """
        # Einfache Heuristik: Enthält der Satz häufig vorkommende deutsche Wörter oder Zeichen?
        deutsche_woerter = {
            'der', 'die', 'und', 'in', 'zu', 'den', 'das', 'ist', 'mit', 'auf', 
            'von', 'für', 'ich', 'nicht', 'dass', 'sie', 'es', 'ein', 'du', 'im', 
            'er', 'an', 'wir', 'was', 'wie', 'haben', 'hat', 'es', 'aber', 'oder', 
            'wenn', 'dann', 'sind', 'bin', 'war', 'sein', 'bei', 'als', 'auch', 
            'noch', 'so', 'nur', 'ja', 'man', 'sich', 'werden', 'können', 'wird', 
            'kann', 'schon', 'mehr', 'jetzt', 'nach', 'wieder'
        }
        return any(wort in satz.lower().split() for wort in deutsche_woerter)
    

    def themen_ermitteln_schlagworte(self, themen_schlagworte: dict[str, list[list[str]]], verbose: bool = False) -> None:
        """
        Ermittelt Themen basierend auf Schlagworten und fügt sie dem Attribut 'themen' hinzu.
        
        :param themen_schlagworte: Dictionary mit Themen und zugehörigen Schlagwortlisten
        :param verbose: Boolescher Wert, der angibt, ob alle Treffer gefunden werden sollen (True) oder ob nach dem ersten Treffer abgebrochen werden soll (False)
        """
        for thema, schlagwortlisten in themen_schlagworte.items():
            if self.saetze:
                for satz in self.saetze:
                    satz_lower = satz.lower()
                    for schlagwortliste in schlagwortlisten:
                        if all(wort in satz_lower for wort in schlagwortliste):
                            self.themen.append(thema)
                            self.thematische_zuordnungen.append((thema, schlagwortliste, satz))
                            if not verbose:
                                break
                    if not verbose and thema in self.themen:
                        break
            else:
                print("Mail.themen_ermitteln_schlagworte: self.saetze enthalten keinen Inhalt.")

    
    def satztrenner(self) -> None:
        """
        Trennt das Attribut 'text' in Sätze auf und speichert sie in der Liste 'saetze'.
        """
        # Regex-Pattern für Satzzeichen, die das Ende eines Satzes markieren
        satzzeichen = re.compile(r'(?<!\d)(?<!\.\d)[.!?](?!\d)(?!\.[a-zA-Z])\s')

        # Trennen des Texts in Sätze
        def split_text(text):
            pos = 0
            saetze = []
            while pos < len(text):
                match = satzzeichen.search(text, pos)
                if not match:
                    saetze.append(text[pos:].strip())
                    break
                end = match.end()
                saetze.append(text[pos:match.start() + 1].strip())  # Ende des Satzes inklusive Satzzeichen
                pos = match.end() - 1  # Start der Suche ab dem Zeichen nach dem Satzzeichen
            return saetze
        
        self.saetze = split_text(self.text)

    
    DEFAULT_EMAIL_PATTERN = re.compile(
        r"""
        (?:(?:mailto:)\s*)?                 # optional: mailto:
        [<(\[\{"]?                          # optional: öffnende Klammer oder Anführungszeichen
        
        (
            [a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+
            @
            [a-zA-Z0-9]
            (?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?
            (?:\.[a-zA-Z0-9]
                (?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?
            )+
        )
        
        [>\)\]\}",;:!?]*                    # optional: schließende Klammern / Satzzeichen
        """,
        re.IGNORECASE | re.VERBOSE
    )

    def referenzen_ermitteln(self, pattern=None, normalisiere_kleinschreibung=True):
        """
        Extrahiert E-Mail-Adressen aus self.text.

        Erkennt u.a.:
        - normale Adressen
        - mailto: Links
        - Adressen in <>, (), [], {}
        - Adressen mit nachgestellten Satzzeichen
        """

        if pattern is None:
            regex = self.DEFAULT_EMAIL_PATTERN
        elif isinstance(pattern, str):
            regex = re.compile(pattern, re.IGNORECASE | re.VERBOSE)
        else:
            regex = pattern

        #----h_ sauberer fassen
        treffer = regex.findall(self.text)

        treffer_temp = []
        for mail_treffer in treffer:
            print(mail_treffer)
            if not mail_treffer.lower() == self.absender.lower():
                treffer_temp.append(mail_treffer)
            else:
                continue

        treffer = treffer_temp

        if normalisiere_kleinschreibung:
            self.referenzen = {mail.lower() for mail in treffer}
        else:
            self.referenzen = set(treffer)

    def referenzen_umgebung_ausgeben(self, context_len=80):
        dicts_list_of_references = []

        for referenz in self.referenzen:
            match_mail = re.search(re.escape(referenz), self.text)

            if not match_mail:
                continue  # optional: robust machen

            beginn_mail = match_mail.start()
            end_mail = match_mail.end()

            umgebung_beginn = max(0, beginn_mail - context_len)
            umgebung_ende = min(len(self.text), end_mail + context_len)

            dicts_list_of_references.append({
                "absender": self.absender,
                "referenz": referenz,
                "text": self.text[umgebung_beginn:umgebung_ende].replace(r"\r|\n", " ")
            })

        return dicts_list_of_references    


    def add_sentiment(self, sentiment_string):
        """
            Übergabe von Sentiment-Werten von außen in die Instanz.
            Vorbereitung für Operationen, mit denen die accuracy der Einstufungsmethoden geprüft werden soll.
        """

        if not isinstance(sentiment_string, str):
            raise TypeError(f"Mail.add_sentiment: Erwartet str, bekommen {type(value).__name__}")
        else:
            self.sentimente.add(sentiment_string)


    def add_match(self, match_objekt):
        """
            Abgleiche von Werten aus der Mail mit externen Quellen.
            Zusammenfassende Speicherung von Instanzen der diversen möglichen Trefferklassen (aktuell nur für Kontakte umgesetzt).

        """
    
        self.matches.add(match_objekt)



class DictForMail:
    """
    Repository-Klasse für Mail-Objekte.

    Attribute:
        _items (Dict[str, Mail]):
            Dictionary mit Absender als Schlüssel und Mail-Instanzen als Werte.

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
        self._items: Dict[str, Mail] = {}
        self.raw_data = raw_data or []
        self.absender: set[str] = set()

    def add(self, obj: Mail) -> None:
        """
        Fügt eine Mail-Instanz hinzu (Key = absender).

        :param obj: Mail-Objekt
        """
        self._items[obj.absender] = obj
        self.absender.add(obj.absender)

    @staticmethod
    def from_raw_data(raw_data: Any, logger, deduplizieren: bool = True) -> "DictForMail":
        """
        Erstellt ein DictForMail-Objekt aus Rohdaten.
        Validiert die Struktur und erzeugt Mail-Instanzen.

        :param raw_data: Liste von 3er-Tupeln/Listen [(absender, betreff, text), ...]
        :param deduplizieren: Wenn True, wird pro Absender nur eine Mail erzeugt
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

        defect_row_counter = {"KeineListe" : 0,
                              "NichtAlleStrings" : 0,
                              "KeineEMailAdresse" : 0,
                              "InstanziierungFehlgeschlagen" : 0} # Keine Liste, Nicht alles Strings, absender keine E-Mail-Adresse, Instanziierung geht fehl

        deduplicated_e_mails = { "counter" : 0}

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

            # --- Deduplizierung ---
            if deduplizieren and absender in repo.absender:
                deduplicated_e_mails["counter"] += 1
                if absender in deduplicated_e_mails.keys():
                    deduplicated_e_mails[absender] += 1
                else:
                    deduplicated_e_mails[absender] = 1
                continue

            # --- Instanziierung ---
            try:
                mail = Mail(absender, betreff, text)
            except:
                defect_row_counter["InstanziierungFehlgeschlagen"] += 1
                logger.info(f"DictForMail.from_raw_data: Instanziierung von Mail-Objekt aus Tupel fehlgeschlagen")

            repo.add(mail)

        
        if deduplizieren:
            logger.info(f"DictForMail.from_raw_data: Deduplizieren aktiv. Für {len(deduplicated_e_mails)} - Adressen wurden {deduplicated_e_mails['counter']} E-Mails ausgeschlossen.")
        frd_counter1 = 0
        for key in defect_row_counter.keys():
            logger.info(f"DictForMail.from_raw_data: Für {defect_row_counter[key]} - Fälle den Fehler {key} erhalten.")
            frd_counter1 += defect_row_counter[key]
        logger.info(f"DictForMail.from_raw_data: {(frd_counter1/len(raw_data))*100:.2f} Fehlerquote.")

        return repo

    def print_thematische_zuordnungen(self) -> None:
        """
        Gibt alle thematischen Zuordnungen aller Mails aus.
        """
        for absender, mail in self._items.items():
            print(f"Absender: {absender}, Betreff: {mail.betreff}")
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

        for absender, mail in self._items.items():
            for thema, schlagwortliste, satz in mail.thematische_zuordnungen:
                data.append([
                    absender,
                    thema,
                    " ".join(schlagwortliste),
                    satz.replace('\n', ' ').replace('\r', '').replace('\t', '')
                ])

        df = pd.DataFrame(
            data,
            columns=['absender', 'thema', 'schlagworte', 'satz']
        )

        df.to_excel(f"{export_folder}/thematische_zuordnungen.xlsx", index=False)

    
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

        # Themen sammeln
        for mail in self._items.values():
            if not mail.themen:
                mails_ohne_thema.append(mail)

            for thema in mail.themen:
                if thema not in themen_dict:
                    themen_dict[thema] = []
                themen_dict[thema].append(mail)

        def _clean_text(text: str) -> str:
            return text.replace("\n", " ").replace(",", "").replace(";", "")

        def _process_match(match) -> dict:
            """
            Wandelt ein Match-Objekt in ein Dictionary um.
            """

            # 🔹 Dataclass prüfen
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

            # 🔹 Fallback für Nicht-Dataclasses
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

        # 🔹 Export je Thema
        for thema, mails_list in themen_dict.items():
            _export_block(mails_list, thema)

        # 🔹 Export ohne Thema
        if mails_ohne_thema:
            _export_block(mails_ohne_thema, "ohne_thema")   

    def export_references_to_excel(self, export_path: str, show_dataframe: bool = False):
        """
            Erstelle eine leere Liste.
            Iteriere über die Mail-Instanzen in self._items und calle referenzen_umgebung_ausgeben.
            Sammle die in Listen organisierten Dictionaries in der erzeugten Liste.
            Erzeuge daraus einen Data Frame.
            Schreibe ihn via .to_excel in den export_path.
        """
        
        liste_ermittelter_referenzen = []
        for mail in self._items.values():
            if mail.referenzen:
                liste_ermittelter_referenzen.extend(mail.referenzen_umgebung_ausgeben())
            else:
                print("DictForMail.export_references_to_excel: Mail-Instanz enthält keine Referenzen.")
        
        referenzen_dict_gekuerzt = pd.DataFrame(liste_ermittelter_referenzen)
        if show_dataframe:
            print(referenzen_dict_gekuerzt.head())
        referenzen_dict_gekuerzt.to_excel(export_path, index=False)


