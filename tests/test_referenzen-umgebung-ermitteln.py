import pytest

from classes.mail import Mail

TEST_CASES = [
    {
        "name": "keine referenzen",
        "text": "Hallo Welt ohne Mailadressen",
        "referenzen": set(),
        "context_len": 5,
    },
    {
        "name": "eine referenz mitte",
        "text": "Hallo xxx a@test.de yyy Ende",
        "referenzen": {"a@test.de"},
        "context_len": 5,
    },
    {
        "name": "eine referenz anfang",
        "text": "a@test.de ist direkt am Anfang",
        "referenzen": {"a@test.de"},
        "context_len": 5,
    },
    {
        "name": "eine referenz ende",
        "text": "Am Ende steht b@test.de",
        "referenzen": {"b@test.de"},
        "context_len": 5,
    },
    {
        "name": "mehrere referenzen verteilt",
        "text": "Kontakt a@test.de und auch b@test.de bitte",
        "referenzen": {"a@test.de", "b@test.de"},
        "context_len": 5,
    },
    {
        "name": "referenzen nah beieinander",
        "text": "a@test.deb@test.de direkt hintereinander",
        "referenzen": {"a@test.de", "b@test.de"},
        "context_len": 5,
    },
    {
        "name": "context groesser als text",
        "text": "kurz a@test.de text",
        "referenzen": {"a@test.de"},
        "context_len": 100,
    },
]


@pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
def test_mail_export(case):
    mail = Mail(
        absender="sender@test.de",
        betreff="Test",
        text=case["text"],
        )

    mail.referenzen=case["referenzen"]
    result = mail.referenzen_umgebung_ausgeben(context_len=case["context_len"])

    text = case["text"]
    referenzen = case["referenzen"]
    context_len = case["context_len"]

    # 🔹 1. Anzahl prüfen
    assert len(result) == len(referenzen)

    # 🔹 2. Struktur prüfen
    for entry in result:
        assert set(entry.keys()) == {"absender", "referenz", "text"}
        assert entry["absender"] == "sender@test.de"

    # 🔹 3. Inhalt prüfen
    for entry in result:
        ref = entry["referenz"]
        snippet = entry["text"]

        # Referenz muss enthalten sein
        assert ref in snippet

        # erwarteten Ausschnitt berechnen
        start_pos = text.index(ref)
        end_pos = start_pos + len(ref) - 1

        expected_start = max(0, start_pos - context_len)
        expected_end = min(len(text), end_pos + context_len + 1)

        expected_snippet = text[expected_start:expected_end]

        expected_snippet = text[expected_start:expected_end]

        assert snippet == expected_snippet

