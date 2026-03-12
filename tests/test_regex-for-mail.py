import pytest

from dein_modul import Mail


@pytest.mark.parametrize(
    "beschreibung, text, erwartet",
    [
        (
            "einfache_mailadressen",
            "Bitte schreibe an max.mustermann@test.de und anna.meier@firma.com.",
            {
                "max.mustermann@test.de",
                "anna.meier@firma.com",
            },
        ),
        (
            "mailto_und_spitze_klammern",
            "Kontakt an <support@unternehmen.org> oder mailto:info@beispiel.de",
            {
                "support@unternehmen.org",
                "info@beispiel.de",
            },
        ),
        (
            "klammern_und_satzzeichen",
            "Empfänger: (vertrieb@firma.de), [hr@firma.de]; <ceo@firma.de>!",
            {
                "vertrieb@firma.de",
                "hr@firma.de",
                "ceo@firma.de",
            },
        ),
        (
            "gross_und_kleinschreibung",
            "Bitte an INFO@BEISPIEL.DE und Sales@Firma.Com senden.",
            {
                "info@beispiel.de",
                "sales@firma.com",
            },
        ),
        (
            "duplikate_werden_entfernt",
            "max@test.de, <max@test.de>, mailto:max@test.de",
            {
                "max@test.de",
            },
        ),
        (
            "keine_mailadresse",
            "Dies ist ein Text ohne gültige Referenzadressen.",
            set(),
        ),
        (
            "gemischter_realistischer_text",
            """
            Hallo Team,

            bitte informiert:
            - Max Mustermann <max@test.de>,
            - den Support unter mailto:support@firma.org,
            - sowie (hr@unternehmen.com).

            Nicht relevant sind: test@localhost und abc@invalid
            Viele Grüße
            """,
            {
                "max@test.de",
                "support@firma.org",
                "hr@unternehmen.com",
            },
        ),
    ],
)
def test_referenzen_ermitteln(beschreibung, text, erwartet):
    mail = Mail(text)
    mail.referenzen_ermitteln()

    assert mail.referenzen == erwartet, (
        f"Fehler im Testfall '{beschreibung}': "
        f"Erwartet {erwartet}, erhalten {mail.referenzen}"
    )