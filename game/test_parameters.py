# pylint:disable=redefined-outer-name
import pytest

from parameters import Parameters

def test_getValue():
    parameters = Parameters()
    assert parameters._getValue("player.maxHealth", "1/2") == 100

def test_getValue_withGlobalEffect():
    parameters = Parameters()
    parameters._addEffect("player.maxHealth", "*/*", "id", "*2")
    assert parameters._getValue("player.maxHealth", "1/2") == 200
    assert parameters._getValue("player.maxHealth", "3/4") == 200

def test_getValue_withGlobalEffectPlus():
    parameters = Parameters()
    parameters._addEffect("player.maxHealth", "*/*", "id", "+20")
    assert parameters._getValue("player.maxHealth", "1/2") == 120

def test_getValue_withGlobalEffectMinus():
    parameters = Parameters()
    parameters._addEffect("player.maxHealth", "*/*", "id", "-20")
    assert parameters._getValue("player.maxHealth", "1/2") == 80

def test_getValue_withGlobalEffectEqual():
    parameters = Parameters()
    parameters._addEffect("player.maxHealth", "*/*", "id", "=150")
    assert parameters._getValue("player.maxHealth", "1/2") == 150

def test_getValue_withGlobalEffectInvalid():
    parameters = Parameters()
    with pytest.raises(Exception):
        parameters._addEffect("player.maxHealth", "*/*", "id", "%150")

def test_getValue_withGlobalEffectMultiple():
    parameters = Parameters()
    parameters._addEffect("player.maxHealth", "*/*", "id", "*2")
    parameters._addEffect("player.maxHealth", "*/*", "id", "+10")
    assert parameters._getValue("player.maxHealth", "1/2") == 210
    assert parameters._getValue("player.maxHealth", "3/4") == 210

def test_getValue_withTeamEffect():
    parameters = Parameters()
    parameters._addEffect("player.maxHealth", "1/*", "id", "*2")
    assert parameters._getValue("player.maxHealth", "1/2") == 200
    assert parameters._getValue("player.maxHealth", "3/4") == 100

def test_getValue_withPlayerEffect():
    parameters = Parameters()
    parameters._addEffect("player.maxHealth", "1/2", "id", "*2")
    assert parameters._getValue("player.maxHealth", "1/1") == 100
    assert parameters._getValue("player.maxHealth", "1/2") == 200
    assert parameters._getValue("player.maxHealth", "3/4") == 100

def test_getValue_removeEffect():
    parameters = Parameters()
    parameters._addEffect("player.maxHealth", "*/*", "id", "*2")
    assert parameters._getValue("player.maxHealth", "1/2") == 200
    parameters._removeEffect("player.maxHealth", "id")
    assert parameters._getValue("player.maxHealth", "1/2") == 100


def test_subscriptions_broadListener(mocker):
    parameters = Parameters()
    listener = mocker.MagicMock()
    listener2 = mocker.MagicMock()
    parameters._subscribeToValue("player.maxHealth", "1/*", listener)
    parameters._subscribeToValue("player.maxHealth", "3/*", listener2)
    parameters._addEffect("player.maxHealth", "1/2", "id", "*2")
    listener.assert_called_once_with("player.maxHealth")
    assert listener2.call_count == 0

    listener.reset_mock()
    parameters._removeEffect("player.maxHealth", "id")
    listener.assert_called_once_with("player.maxHealth")
    assert listener2.call_count == 0

def test_subscriptions_broadEffect(mocker):
    parameters = Parameters()
    listener = mocker.MagicMock()
    listener2 = mocker.MagicMock()
    parameters._subscribeToValue("player.maxHealth", "1/2", listener)
    parameters._subscribeToValue("player.maxHealth", "3/4", listener2)
    parameters._addEffect("player.maxHealth", "1/*", "id", "*2")
    listener.assert_called_once_with("player.maxHealth")
    assert listener2.call_count == 0

    listener.reset_mock()
    parameters._removeEffect("player.maxHealth", "id")
    listener.assert_called_once_with("player.maxHealth")
    assert listener2.call_count == 0

