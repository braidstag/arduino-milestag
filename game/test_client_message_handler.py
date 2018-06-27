"Test how the client handles messages from the server"

from client import Client, Main
import proto

def noop():
    "No op function for use as a stub"
    pass

def test_ping(mocker):
    "Test handling of PING message"
    mocker.patch.object(Client, '_openConnection', autospec=True)
    client_obj = Client(mocker.MagicMock())
    mocker.patch.object(client_obj, 'queueMessage', autospec=True)
    assert client_obj.handleMsg("E(123def,1516565652,Ping())")
    client_obj.queueMessage.assert_called_once_with("Pong(1516565652,0)")

def test_simple_pong(mocker):
    "Test handling of PONG message which doesn't need a response"
    mocker.patch.object(Client, '_openConnection', autospec=True)
    client_obj = Client(mocker.MagicMock(), timeProvider=lambda: 1516566052)
    mocker.patch.object(client_obj, 'queueMessage', autospec=True)
    assert client_obj.handleMsg("E(123def,1516565852,Pong(1516565652,0))")

def test_reply_pong(mocker):
    "Test handling of PONG message which requests a response"
    mocker.patch.object(Client, '_openConnection', autospec=True)
    client_obj = Client(mocker.MagicMock(), timeProvider=lambda: 1516566052)
    mocker.patch.object(client_obj, 'queueMessage', autospec=True)
    assert client_obj.handleMsg("E(123def,1516565852,Pong(1516565652,1))")
    client_obj.queueMessage.assert_called_once_with("Pong(1516565852,0)")
