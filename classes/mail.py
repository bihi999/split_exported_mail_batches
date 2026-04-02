import re
from typing import List, Tuple, Dict, Any
import pandas as pd


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
        
        self.saetze = []  # Neues Attribut für alle Sätze
        self.deutsche_saetze = []
        self.themen = []  # Neues Attribut für Themen
        self.kunde = False
        self.status = ""  # Initialisiert als leerer String
        self.webid = set()
        self.thematische_zuordnungen = []  # Neues Attribut für thematische Zuordnungen
        self.referenzen = set()

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

        treffer = regex.findall(self.text)

        if normalisiere_kleinschreibung:
            self.referenzen = {mail.lower() for mail in treffer}
        else:
            self.referenzen = set(treffer)

    def referenzen_umgebung_ausgeben(self, context_len=10):
        dicts_list_of_references = []

        for referenz in self.referenzen:
            match_mail = re.search(re.escape(referenz), self.text)

            if not match_mail:
                continue  # optional: robust machen

            beginn_mail = match_mail.start()
            end_mail = match_mail.end()

            # Ausdruck unklar
            umgebung_beginn = max(0, beginn_mail - context_len)
            umgebung_ende = min(len(self.text), end_mail + context_len)

            dicts_list_of_references.append({
                "absender": self.absender,
                "referenz": referenz,
                "text": self.text[umgebung_beginn:umgebung_ende],
            })

        return dicts_list_of_references    


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
    def from_raw_data(raw_data: Any, deduplizieren: bool = True) -> "DictForMail":
        """
        Erstellt ein DictForMail-Objekt aus Rohdaten.

        Validiert die Struktur und erzeugt Mail-Instanzen.

        :param raw_data: Liste von 3er-Tupeln/Listen:
                         [(absender, betreff, text), ...]
        :param deduplizieren: Wenn True, wird pro Absender nur eine Mail erzeugt
        :return: Instanz von DictForMail
        :raises ValueError: bei ungültiger Struktur oder ungültiger E-Mail
        """

        # --- Validierung Grundstruktur ---
        if not isinstance(raw_data, list):
            raise ValueError("raw_data muss eine Liste sein")

        # Regex aus Mail-Klasse verwenden
        email_pattern = Mail.DEFAULT_EMAIL_PATTERN

        repo = DictForMail(raw_data=raw_data)

        for entry in raw_data:
            if not isinstance(entry, (list, tuple)) or len(entry) != 3:
                raise ValueError(
                    "Jeder Eintrag muss ein 3er-Tupel oder Liste sein (absender, betreff, text)"
                )

            absender, betreff, text = entry

            # --- Typprüfung ---
            if not all(isinstance(x, str) for x in entry):
                #raise ValueError("Alle Elemente müssen Strings sein")
                continue

            # --- Validierung absender (E-Mail-Pattern) ---
            if not email_pattern.search(absender):
                #raise ValueError("Ungültige E-Mail-Adresse: {}".format(absender))
                continue
                
            # --- Deduplizierung ---
            if deduplizieren and absender in repo.absender:
                continue

            # --- Instanziierung ---
            mail = Mail(absender, betreff, text)
            repo.add(mail)

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