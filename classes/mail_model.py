import re
from typing import ClassVar


class Mail:
    """
    Repräsentiert eine E-Mail mit Absender, Betreff und Text.
    """
    _next_id: ClassVar[int] = 1

    def __init__(self, absender: str, betreff: str, text: str):
        """
        Initialisiert eine Mail-Instanz.

        :param absender: Absender der E-Mail
        :param betreff: Betreff der E-Mail
        :param text: Text der E-Mail
        """
        self.id = Mail._next_id
        Mail._next_id += 1

        self.absender = absender
        self.betreff = betreff
        self.text = text

        self.saetze = []

        #--------       self.deutsche_saetze = [] - Logik unklar - Redundanz und zugleich Nutzen unklar.

        self.sentimente = set()     # Jede Testfunktion setzt voraus dass der E-Mail von außen bereits ermittelte Sentimente übergeben werden können

        #--------       self.kunde = False - Eine Mail hat keine Kundeneigenschaft
        #--------       self.status = "" - Eine Mail hat keinen Aktivitätsstatus
        #--------       self.webid = set() - Eine Mail hat selbst keine direkte Verbindung zu einer WebID

        self.thematische_zuordnungen = []  # Treffer werden hier hinterlegt - also die Zuordnung von Text zu einem bestimmten Sentiment - die Tupel-Struktur der Schlagwortmethode muss noch generalisiert werden
        self.referenzen = set()   # Menge zum Speichern von Mailadressen die in der E-Mail erwähnt werden

        self.matches = set()   # Abgleich aus der Mail heraus führen zu Treffer-Objekten die hier gespeichert werden

    def _deduplizierungs_key(self) -> tuple[str, str, str]:
        return (
            self.absender.strip().casefold(),
            self.betreff.strip(),
            self.text.strip()
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Mail):
            return NotImplemented

        return self._deduplizierungs_key() == other._deduplizierungs_key()

    def __hash__(self) -> int:
        return hash(self._deduplizierungs_key())

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
        Ermittelt Themen basierend auf Schlagworten und fügt Treffer den thematischen Zuordnungen hinzu.

        :param themen_schlagworte: Dictionary mit Themen und zugehörigen Schlagwortlisten
        :param verbose: Boolescher Wert, der angibt, ob alle Treffer gefunden werden sollen (True) oder ob nach dem ersten Treffer abgebrochen werden soll (False)
        """
        for thema, schlagwortlisten in themen_schlagworte.items():
            if self.saetze:
                thema_gefunden = False
                for satz in self.saetze:
                    satz_lower = satz.lower()
                    for schlagwortliste in schlagwortlisten:
                        if all(wort in satz_lower for wort in schlagwortliste):
                            self.thematische_zuordnungen.append((thema, schlagwortliste, satz))
                            thema_gefunden = True
                            if not verbose:
                                break
                    if not verbose and thema_gefunden:
                        break
            else:
                print("Mail.themen_ermitteln_schlagworte: self.saetze enthalten keinen Inhalt.")

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
