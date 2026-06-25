import pandas as pd
import pytest

from klickertool.klickertool import (
    DataFrameSource,
    DataFrameSourceConfig,
    KlickerConfig,
    SelectionRepository,
)


class DummyLogger:
    def __init__(self):
        self.errors = []
        self.infos = []

    def error(self, message):
        self.errors.append(message)

    def info(self, message):
        self.infos.append(message)


def make_repository(dataframe, logger=None):
    config = KlickerConfig(
        output_path="klickertool_test_results.xlsx",
        group_column="gruppe",
        display_columns=["gruppe", "wert"],
        status_column="status",
        done_value="done",
    )
    source = DataFrameSource(DataFrameSourceConfig(dataframe=dataframe), logger=logger)
    return SelectionRepository(source, config, logger=logger)


def test_selection_repository_returns_next_unprocessed_group():
    dataframe = pd.DataFrame(
        [
            {"gruppe": 1, "wert": "A", "status": "done"},
            {"gruppe": 2, "wert": "B", "status": ""},
            {"gruppe": 2, "wert": "C", "status": ""},
        ]
    )

    repository = make_repository(dataframe)
    group_name, group_data = repository.get_next_group()

    assert group_name == 2
    assert group_data["wert"].tolist() == ["B", "C"]


@pytest.mark.parametrize(
    "dataframe, expected_message",
    [
        (
            pd.DataFrame([{"wert": "A", "status": ""}]),
            "Pflichtspalten fehlen",
        ),
        (
            pd.DataFrame([{"gruppe": 1, "status": ""}]),
            "Anzeigespalten fehlen",
        ),
        (
            pd.DataFrame([{"gruppe": None, "wert": "A", "status": ""}]),
            "Gruppierung nicht moeglich",
        ),
    ],
)
def test_selection_repository_validates_grouping_requirements(dataframe, expected_message):
    logger = DummyLogger()

    with pytest.raises(ValueError, match=expected_message):
        make_repository(dataframe, logger=logger)

    assert logger.errors
    assert expected_message in logger.errors[0]
