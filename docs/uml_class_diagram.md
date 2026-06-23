# UML-Klassendiagramme

Die Diagramme bilden die produktiven Klassen aus `classes/` ab. Ausgenommen sind Testcode, der Ordner `hilfsfunktionen/` sowie freie Hilfsfunktionen und Ablaufcode aus `main.py`.

Fuer Mermaid-Renderer, die kein Markdown parsen, liegen die Diagramme zusaetzlich einzeln ohne Code-Fences vor:
`docs/uml_overview.mmd`, `docs/uml_packages.mmd` und `docs/uml_flow.mmd`.

## Gesamtuebersicht

```mermaid
classDiagram
    direction LR

    class Mail {
        +ClassVar~int~ _next_id
        +int id
        +str absender
        +str betreff
        +str text
        +list saetze
        +set sentimente
        +list thematische_zuordnungen
        +set referenzen
        +set matches
        +Pattern DEFAULT_EMAIL_PATTERN
        +__init__(absender: str, betreff: str, text: str)
        -_deduplizierungs_key() tuple
        +satztrenner() None
        +is_probably_german(satz: str) bool
        +themen_ermitteln_schlagworte(themen_schlagworte: dict, verbose: bool) None
        +referenzen_ermitteln(pattern=None, normalisiere_kleinschreibung=True)
        +referenzen_umgebung_ausgeben(logger, context_len=80) list
        +add_sentiment(sentiment_string)
        +add_match(match_objekt)
    }

    class DictForMail {
        -Dict~int, Mail~ _items
        +list raw_data
        +set~str~ absender
        +__init__(raw_data: list = None)
        +add(obj: Mail) None
        +from_raw_data(raw_data: Any, logger) DictForMail
        +deduplizieren() DictForMail
        +print_thematische_zuordnungen() None
        +export_thematische_zuordnungen_to_excel(export_folder: str) None
        +export_mails_to_excel(export_path: str) None
        +export_references_to_excel(export_path: str, logger, show_dataframe: bool)
    }

    class ValidationResult {
        +bool is_valid
        +List~str~ errors
    }

    class CSVHandler {
        +str filepath
        +str encoding
        +str content
        +set exceptions
        +__init__(filepath: str, encoding: str, content: str)
        +validate_file(filepath: str, logger, expected_encoding: str) ValidationResult
        +from_file(filepath: str, encoding: str) CSVHandler
        +csv_to_pandas(sep) DataFrame
        +transform_pandas(df, mapping: dict, use_case: str) DataFrame
        +split_content(separators: list~str~) tuple
    }

    class ContactMatch {
        +Optional~bool~ kunde
        +str status
        +str webid
        +str source
        +__post_init__()
        -_validate_kunde(value) Optional~bool~
        -_validate_webid(value) str
    }

    class Matcher {
        <<abstract>>
        +find(absender: str) List~ContactMatch~
    }

    class DictionaryMatcher {
        +dict dwh_dict
        +__init__(dwh_dict)
        +find(absender: str) List~ContactMatch~
    }

    DictForMail "1" o-- "*" Mail : verwaltet
    Mail "1" o-- "*" ContactMatch : matches
    CSVHandler ..> ValidationResult : validiert als
    DictForMail ..> CSVHandler : nutzt Rohdaten aus
    DictForMail ..> Mail : erzeugt
    DictionaryMatcher --|> Matcher
    Matcher ..> ContactMatch : liefert
    DictionaryMatcher ..> ContactMatch : erzeugt
```

## Paketstruktur

```mermaid
classDiagram
    namespace classes.mail_model {
        class Mail
    }

    namespace classes.mail_repository {
        class DictForMail
    }

    namespace classes.csvfile {
        class ValidationResult
        class CSVHandler
    }

    namespace classes.matches {
        class ContactMatch
        class Matcher
        class DictionaryMatcher
    }

    DictForMail "1" o-- "*" Mail
    Mail "1" o-- "*" ContactMatch
    DictionaryMatcher --|> Matcher
    Matcher ..> ContactMatch
```

## Fachlicher Ablauf

```mermaid
classDiagram
    direction TB

    class CSVHandler {
        +validate_file(...)
        +from_file(...)
        +csv_to_pandas(...)
        +transform_pandas(...)
        +split_content(...)
    }

    class DictForMail {
        +from_raw_data(...)
        +deduplizieren()
        +export_thematische_zuordnungen_to_excel(...)
        +export_mails_to_excel(...)
        +export_references_to_excel(...)
    }

    class Mail {
        +satztrenner()
        +themen_ermitteln_schlagworte(...)
        +referenzen_ermitteln(...)
        +add_match(...)
    }

    class Matcher {
        <<abstract>>
        +find(absender: str)
    }

    class DictionaryMatcher {
        +find(absender: str)
    }

    class ContactMatch {
        +kunde
        +status
        +webid
        +source
    }

    CSVHandler ..> DictForMail : liefert gesplittete Rohdaten
    DictForMail "1" o-- "*" Mail : erzeugt und speichert
    Mail ..> Matcher : Abgleich ueber absender
    DictionaryMatcher --|> Matcher
    DictionaryMatcher ..> ContactMatch : Ergebnis
    Mail "1" o-- "*" ContactMatch : speichert
```
