from classes.mail import DictForMail


class DummyLogger:
    def info(self, message):
        pass


def test_from_raw_data_keeps_multiple_mails_from_same_sender():
    raw_data = [
        ["sender@test.de", "Betreff A", "Text A"],
        ["sender@test.de", "Betreff B", "Text B"],
    ]

    repo = DictForMail.from_raw_data(raw_data, DummyLogger())

    assert len(repo._items) == 2
    assert [mail.betreff for mail in repo._items.values()] == ["Betreff A", "Betreff B"]


def test_deduplizieren_removes_equal_mails_by_mail_definition():
    raw_data = [
        ["sender@test.de", "Betreff", "Text"],
        ["SENDER@test.de", "Betreff", "Text"],
        ["sender@test.de", "Anderer Betreff", "Text"],
    ]

    repo = DictForMail.from_raw_data(raw_data, DummyLogger())
    dedupliziert = repo.deduplizieren()

    assert len(repo._items) == 3
    assert len(dedupliziert._items) == 2
    assert [mail.betreff for mail in dedupliziert._items.values()] == [
        "Betreff",
        "Anderer Betreff",
    ]
