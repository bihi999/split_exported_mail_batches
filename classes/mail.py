import re


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