from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List


# =========================================================
# 🔹 1. DOMAIN-OBJEKT: ContactMatch
# =========================================================

@dataclass
class ContactMatch:
    """
    Repräsentiert das Ergebnis eines Matchings für eine Mailadresse.
    """

    kunde: bool | None
    status: str
    webid: str           # ❗ Pflichtfeld (kein Optional mehr)
    source: str

    def __post_init__(self):
        """
        Wird automatisch nach dem von @dataclass generierten __init__ aufgerufen.

        👉 Antwort auf deine Frage:
        - __post_init__ ist ein offizieller Hook von dataclasses
        - läuft DIREKT nach Initialisierung
        - wenn hier eine Exception fliegt → Objekt wird NICHT erfolgreich erzeugt

        => Es entstehen KEINE „halb-validen“ Objekte im System
        """
        self.kunde = self._validate_kunde(self.kunde)
        self.webid = self._validate_webid(self.webid)

    def _validate_kunde(self, value) -> bool | None:
        """
        Validierung für kunde.

        Anforderungen:
        - bool bleibt bool
        - konvertierbare Werte erlaubt (1, 0, "true", "false", ...)
        - sonst Fehler
        """

        if value is None:
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, (int, str)):
            str_val = str(value).strip().lower()

            if str_val in {"1", "true", "yes"}:
                return True
            if str_val in {"0", "false", "no"}:
                return False

        raise ValueError(f"Ungültiger Wert für kunde: {value}")

    def _validate_webid(self, value) -> str:
        """
        Validierung für webid.

        👉 Antwort auf deine Frage:
        - webid ist jetzt Pflichtfeld → Optional entfernt
        - daher darf value NICHT None sein

        Anforderungen:
        - muss String sein
        - darf nicht leer sein
        - muss vollständig in int konvertierbar sein
        """

        if value is None:
            raise ValueError("webid ist verpflichtend und darf nicht None sein")

        if not isinstance(value, str):
            raise ValueError(f"webid muss ein String sein, ist aber: {type(value)}")

        value = value.strip()

        if value == "":
            raise ValueError("webid darf nicht leer sein")

        try:
            int(value)
        except ValueError:
            raise ValueError(f"webid ist keine gültige Ganzzahl: {value}")

        return value


# =========================================================
# 🔹 2. STRATEGY INTERFACE
# =========================================================

class Matcher(ABC):
    """
    Strategy-Interface.
    Definiert den Vertrag für alle Matcher.

    Subclasses überschreiben jeweils die find - Methode.
    Methode ist in der Elternklasse nur zum Auslösen einer Exception vorhanden.
    Matcher bezieht sich immer auf "absender" - das ist der "Vertrag".
    Matcher ist gebunden an ContactMatch.
    Nicht vollkommen entkoppelt dadurch.

    """

    @abstractmethod
    def find(self, absender: str) -> List[ContactMatch]:
        raise NotImplementedError("Must be implemented by subclass")


# =========================================================
# 🔹 3. KONKRETE STRATEGY: DictionaryMatcher
# =========================================================

class DictionaryMatcher(Matcher):
    """
    Implementiert Matching gegen ein Dictionary (z. B. aus CSV geladen).
    """

    def __init__(self, dwh_dict):
        self.dwh_dict = dwh_dict

    def find(self, absender: str) -> List[ContactMatch]:

        # ❌ Kein Treffer im DWH
        if absender not in self.dwh_dict:
            return [
                ContactMatch(
                    kunde=None,
                    status="ohne_dwh_abgleich",
                    webid="0",  # ❗ Pflichtfeld → muss gesetzt werden
                    source="DWH_DICT"
                )
            ]

        mail_data = self.dwh_dict[absender]

        # -------------------------
        # kunde bestimmen
        # -------------------------
        if 1 in mail_data.get('kunde', set()):
            kunde = True
        elif 0 in mail_data.get('kunde', set()):
            kunde = False
        else:
            kunde = None

        # -------------------------
        # status bestimmen
        # -------------------------
        status = ""
        if 'status_key' in mail_data:
            status_values = mail_data['status_key']
            if len(status_values) == 1 and 'inaktiv' in status_values:
                status = 'inaktiv'
            elif len(status_values) > 0:
                status = 'aktiv'

        # -------------------------
        # webid bestimmen
        # -------------------------
        webid_set = mail_data.get('webid', None)

        if not webid_set:
            # 👉 Designentscheidung:
            # Wenn webid Pflicht ist, darf es eigentlich kein Match ohne webid geben
            # Hier setzen wir einen Fallback – alternativ: KEIN Match zurückgeben
            webid = "0"
        else:
            webid = next(iter(webid_set))  # einfacher erster Wert

        return [
            ContactMatch(
                kunde=kunde,
                status=status,
                webid=webid,
                source="DWH_DICT"
            )
        ]
