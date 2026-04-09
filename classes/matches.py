from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List


# =========================================================
# 🔹 1. DOMAIN-OBJEKT: ContactMatch
# =========================================================

from dataclasses import dataclass


@dataclass(frozen=True) # Ohne frozen not hashable - ohne Hash kann __eq__ nicht erfolgreich definiert werden - ohne __eq__ keine .add() auf Ergebnismengen
class ContactMatch:
    kunde: bool | None
    status: str
    webid: str
    source: str

    def __post_init__(self):
        # ❗ trotz frozen=True erlaubt via object.__setattr__
        object.__setattr__(self, "kunde", self._validate_kunde(self.kunde))
        object.__setattr__(self, "webid", self._validate_webid(self.webid))

    # 🔹 Gleichheit NUR über webid + source
    def __eq__(self, other):
        if not isinstance(other, ContactMatch):
            return NotImplemented
        return (self.webid, self.source) == (other.webid, other.source)

    # 🔹 Hash konsistent zur Gleichheit
    def __hash__(self):
        return hash((self.webid, self.source))

    def _validate_kunde(self, value) -> bool | None:
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
        if value is None:
            raise ValueError("webid ist verpflichtend")

        if not isinstance(value, str):
            raise ValueError("webid muss String sein")

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
