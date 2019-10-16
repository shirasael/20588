import time
import mock
from scapy.compat import raw
from datetime import datetime
from common.signal_protocol import SignalPacket, PLAY_SIGNAL, DEFAULT_WAIT_SECONDS, STOP_SIGNAL
from server.music_server import MusicServer, Entity


def call_counter(func):
    def helper(*args, **kwargs):
        helper.calls += 1
        return func(*args, **kwargs)

    helper.calls = 0
    helper.__name__ = func.__name__
    return helper


@mock.patch('socket.socket')
def test_accept_multiple_clients(mock_socket):
    print("Mocking 2 clients")
    accept_mock_values = [(mock.Mock(), ("1.1.1.1", 12345)),
                          (mock.Mock(), ("2.2.2.2", 23456))]

    @call_counter
    def accept_side_effect():
        if accept_side_effect.calls > 2:
            time.sleep(1)
        else:
            return accept_mock_values[accept_side_effect.calls - 1]

    mock_socket.return_value.accept.side_effect = accept_side_effect

    tested_server = MusicServer('1.2.3.4', 12345)
    tested_server.start()
    tested_server.stop()
    assert tested_server.clients == {
        Entity("1.1.1.1", 12345): accept_mock_values[0][0],
        Entity("2.2.2.2", 23456): accept_mock_values[1][0]
    }


@mock.patch('socket.socket')
def test_accept_multiple_clients_duplicates(mock_socket):
    print("Mocking 2 clients")
    accept_mock_values = [(mock.Mock(), ("1.1.1.1", 12345)),
                          (mock.Mock(), ("2.2.2.2", 23456))]

    @call_counter
    def accept_side_effect():
        if accept_side_effect.calls > 4:
            time.sleep(1)
        else:
            return accept_mock_values[(accept_side_effect.calls - 1) % 2]

    mock_socket.return_value.accept.side_effect = accept_side_effect

    tested_server = MusicServer('1.2.3.4', 12345)
    tested_server.start()
    tested_server.stop()
    assert mock_socket.return_value.accept.call_count >= 4
    assert tested_server.clients == {
        Entity("1.1.1.1", 12345): accept_mock_values[0][0],
        Entity("2.2.2.2", 23456): accept_mock_values[1][0]
    }


@mock.patch('socket.socket')
def test_signal_play_all(_):
    tested_server = MusicServer('1.2.3.4', 12345)
    tested_server.clients = {
        Entity("1.1.1.1", 12345): mock.Mock(),
        Entity("2.2.2.2", 23456): mock.Mock(),
        Entity("3.3.3.3", 45632): mock.Mock(),
        Entity("4.4.4.4", 54321): mock.Mock()
    }
    dummy_path = "C:\\bla.mp3"
    now = datetime.now()
    expected_message = SignalPacket(signal=PLAY_SIGNAL,
                                    send_timestamp=now.timestamp(),
                                    wait_seconds=DEFAULT_WAIT_SECONDS,
                                    music_file_path=dummy_path)

    with mock.patch('server.music_server.datetime') as mock_datetime:
        mock_datetime.now.return_value = now
        tested_server.signal_play_all(dummy_path)

    for _, mock_client in tested_server.clients.items():
        mock_client.send.assert_called_once_with(raw(expected_message))


@mock.patch('socket.socket')
def test_signal_stop_all(_):
    tested_server = MusicServer('1.2.3.4', 12345)
    tested_server.clients = {
        Entity("1.1.1.1", 12345): mock.Mock(),
        Entity("2.2.2.2", 23456): mock.Mock(),
        Entity("3.3.3.3", 45632): mock.Mock(),
        Entity("4.4.4.4", 54321): mock.Mock()
    }
    now = datetime.now()
    expected_message = SignalPacket(signal=STOP_SIGNAL,
                                    send_timestamp=now.timestamp(),
                                    wait_seconds=DEFAULT_WAIT_SECONDS,
                                    music_file_path="")

    with mock.patch('server.music_server.datetime') as mock_datetime:
        mock_datetime.now.return_value = now
        tested_server.signal_stop_all()

    for _, mock_client in tested_server.clients.items():
        mock_client.send.assert_called_once_with(raw(expected_message))
