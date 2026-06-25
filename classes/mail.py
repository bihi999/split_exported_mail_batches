from classes.mail_model import Mail
from classes.mail_repository import DictForMail


def export_selected_sentences(mail_dict: DictForMail, export_path: str, logger, sentiment: str) -> None:
    """
    Provisorischer Workflow zur manuellen Satzauswahl je Mail.
    """
    from pathlib import Path

    import pandas as pd

    selected_sentences = {}
    result_counter = 0

    export_file = Path(export_path)
    if export_file.suffix.lower() not in {".xlsx", ".xls"}:
        export_file = export_file / "selected_sentences.xlsx"

    for mail in mail_dict._items.values():
        sentences = DictForMail.SplitTextbodyIntoSentences(mail.text, logger)
        sentence_options = DictForMail.BuildIterableForStrings(
            limit_sentence_count=5,
            limit_sentence_length=23,
            sentences=sentences,
            logger=logger,
        )

        if not sentence_options:
            logger.info(f"export_selected_sentences: Keine auswählbaren Sätze für Mail-ID {mail.id}.")
            continue

        print(f"\nAbsender: {mail.absender}")
        print(f"Betreff: {mail.betreff}")
        for key, sentence in sentence_options.items():
            print(f"{key}: {sentence}")

        while True:
            user_input = input("Satznummer wählen, 's' überspringen, 'a' abbrechen: ").strip().lower()

            if user_input == "a":
                logger.info("export_selected_sentences: Manuelle Auswahl wurde abgebrochen.")
                df = pd.DataFrame.from_dict(selected_sentences, orient="index")
                df.to_excel(export_file, index=False)
                return

            if user_input == "s":
                logger.info(f"export_selected_sentences: Mail-ID {mail.id} wurde übersprungen.")
                break

            try:
                selected_key = int(user_input)
            except ValueError:
                print("Fehler: Bitte eine Zahl, 's' oder 'a' eingeben.")
                continue

            if selected_key not in sentence_options:
                print("Fehler: Die gewählte Zahl ist kein vorhandener Schlüssel.")
                continue

            selected_sentences[result_counter] = {
                "absender": mail.absender,
                "sentiment": sentiment,
                "satz": sentence_options[selected_key],
            }
            result_counter += 1
            break

    df = pd.DataFrame.from_dict(selected_sentences, orient="index")
    df.to_excel(export_file, index=False)


__all__ = ["Mail", "DictForMail", "export_selected_sentences"] # Reminder: Kontrolle des Exports
