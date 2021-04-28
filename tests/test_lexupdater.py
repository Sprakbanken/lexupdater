"""
Test suite for the __main__.py script in the lexupdater package
"""
from unittest.mock import patch

import pytest
import lexupdater
import runpy

@pytest.mark.skip("Refactor module structure before updating the test")
def test_get_base(db_updater_obj):
    # given
    input_connection = db_updater_obj.get_connection()
    # when
    result = None  # lexupdater.get_base(input_connection)
    # then
    assert isinstance(result, list)
    assert "word_id" in result[0]
    assert "wordform" in result[0]
    assert "pos" in result[0]


@pytest.mark.skip("Refactor module structure before updating the test")
def test_main_script(db_updater_obj):
    with patch.object(lexupdater.DatabaseUpdater, "get_connection",
                      new_callable=db_updater_obj.get_connection) as db_obj:
        # when
        runpy.run_module("lexupdater")
        # then
        db_obj.assert_called()
