import pytest
import sys
import types

from classes.mail_repository import DictForMail


class DummyLogger:
    def __init__(self):
        self.errors = []

    def error(self, message):
        self.errors.append(message)


@pytest.fixture
def fake_spacy_blank(monkeypatch):
    class FakeSentence:
        def __init__(self, text):
            self.text = text

    class FakeDoc:
        def __init__(self, sentences):
            self.sents = [FakeSentence(sentence) for sentence in sentences]

    class FakeNlp:
        def __init__(self):
            self.pipe_names = []

        def add_pipe(self, pipe_name):
            self.pipe_names.append(pipe_name)

        def __call__(self, text):
            sentences = [
                sentence
                for sentence in text.split("|")
                if sentence.strip()
            ]
            return FakeDoc(sentences)

    fake_spacy = types.SimpleNamespace(blank=lambda language: FakeNlp())
    monkeypatch.setitem(sys.modules, "spacy", fake_spacy)


@pytest.fixture
def sentence_lists_for_build_iterable():
    return [
        {
            "name": "begrenzt_auf_zwei_kurze_saetze",
            "sentences": [
                "Kurz.",
                "Dieser Satz hat zu viele Woerter fuer das gesetzte Limit.",
                "Passt auch.",
                "Dieser Satz wird wegen limit_sentence_count nicht mehr aufgenommen.",
            ],
            "limit_sentence_count": 2,
            "limit_sentence_length": 3,
            "expected": {
                0: "Kurz.",
                1: "Passt auch.",
            },
        },
        {
            "name": "ignoriert_alle_zu_langen_saetze",
            "sentences": [
                "Dieser Satz ist deutlich zu lang.",
                "Auch dieser Satz hat zu viele Woerter.",
            ],
            "limit_sentence_count": 3,
            "limit_sentence_length": 2,
            "expected": {},
        },
        {
            "name": "nimmt_nur_bis_zum_count_limit",
            "sentences": [
                "Satz null.",
                "Satz eins.",
                "Satz zwei.",
            ],
            "limit_sentence_count": 2,
            "limit_sentence_length": 3,
            "expected": {
                0: "Satz null.",
                1: "Satz eins.",
            },
        },
    ]


@pytest.mark.parametrize("invalid_sentences", [
    "Kein Listenobjekt.",
    ["Gueltiger Satz.", 42],
    None,
])
def test_build_iterable_for_strings_logs_error_for_invalid_input(invalid_sentences):
    logger = DummyLogger()

    result = DictForMail.BuildIterableForStrings(
        limit_sentence_count=2,
        limit_sentence_length=5,
        sentences=invalid_sentences,
        logger=logger,
    )

    assert result == {}
    assert logger.errors == ["BuildIterableForStrings: Erwartet eine Liste mit Strings."]


def test_build_iterable_for_strings_filters_and_numbers_sentences(sentence_lists_for_build_iterable):
    for case in sentence_lists_for_build_iterable:
        result = DictForMail.BuildIterableForStrings(
            limit_sentence_count=case["limit_sentence_count"],
            limit_sentence_length=case["limit_sentence_length"],
            sentences=case["sentences"],
        )

        assert result == case["expected"], f"Fehler im Testfall {case['name']}"


@pytest.fixture
def textbody_sentence_split_cases():
    return [
        {
            "name": "mehrere_saetze",
            "text": "Erster Satz.| Zweiter Satz! |Dritter Satz?",
            "expected": ["Erster Satz.", "Zweiter Satz!", "Dritter Satz?"],
        },
        {
            "name": "leere_teile_werden_ignoriert",
            "text": "Erster Satz.|| Zweiter Satz.",
            "expected": ["Erster Satz.", "Zweiter Satz."],
        },
    ]


def test_split_textbody_into_sentences_uses_spacy_blank(fake_spacy_blank, textbody_sentence_split_cases):
    logger = DummyLogger()

    for case in textbody_sentence_split_cases:
        result = DictForMail.SplitTextbodyIntoSentences(case["text"], logger)

        assert result == case["expected"], f"Fehler im Testfall {case['name']}"
        assert logger.errors == []


def test_split_textbody_into_sentences_logs_error_when_spacy_fails(monkeypatch):
    logger = DummyLogger()

    def raise_error(language):
        raise RuntimeError("spacy nicht verfuegbar")

    fake_spacy = types.SimpleNamespace(blank=raise_error)
    monkeypatch.setitem(sys.modules, "spacy", fake_spacy)

    result = DictForMail.SplitTextbodyIntoSentences("Ein Satz.", logger)

    assert result == []
    assert len(logger.errors) == 1
    assert logger.errors[0].startswith("SplitTextbodyIntoSentences:")
