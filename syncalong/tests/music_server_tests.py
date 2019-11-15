import os
import time
import mock
from datetime import datetime
from common.signal_packet import SignalPacket, PLAY_SIGNAL, DEFAULT_WAIT_SECONDS, STOP_SIGNAL
from server.music_server import MusicServer


def call_counter(func):
    def helper(*args, **kwargs):
        helper.calls += 1
        return func(*args, **kwargs)

    helper.calls = 0
    helper.__name__ = func.__name__
    return helper


@mock.patch('server.music_server.LengthSocket')
def test_accept_multiple_clients(mock_socket):
    print("Mocking 2 clients")
    accept_mock_values = [mock.Mock(), mock.Mock()]

    @call_counter
    def accept_side_effect():
        if accept_side_effect.calls > 2:
            time.sleep(1)
        else:
            return accept_mock_values[accept_side_effect.calls - 1], ('1.1.1.1', 11111)

    mock_socket.return_value.accept.side_effect = accept_side_effect

    tested_server = MusicServer('1.2.3.4', 12345)
    tested_server.start()
    tested_server.stop()
    assert tested_server.clients == accept_mock_values


@mock.patch('server.music_server.LengthSocket')
def test_signal_play_all(_):
    tested_server = MusicServer('1.2.3.4', 12345)
    tested_server.clients = [mock.Mock() for _ in range(4)]
    dummy_path = "C:\\bla.mp3"
    now = datetime.now()
    expected_message = SignalPacket(signal=PLAY_SIGNAL,
                                    send_timestamp=now.timestamp(),
                                    wait_seconds=DEFAULT_WAIT_SECONDS,
                                    music_file_name=os.path.basename(dummy_path))

    with mock.patch('server.music_server.datetime') as mock_datetime:
        mock_datetime.now.return_value = now
        tested_server.signal_play_all(dummy_path)

    for mock_client in tested_server.clients:
        mock_client.send.assert_called_once_with(expected_message)


@mock.patch('server.music_server.LengthSocket')
def test_signal_stop_all(_):
    tested_server = MusicServer('1.2.3.4', 12345)
    tested_server.clients = [mock.Mock() for _ in range(4)]
    now = datetime.now()
    expected_message = SignalPacket(signal=STOP_SIGNAL,
                                    send_timestamp=now.timestamp(),
                                    wait_seconds=DEFAULT_WAIT_SECONDS,
                                    music_file_name="")

    with mock.patch('server.music_server.datetime') as mock_datetime:
        mock_datetime.now.return_value = now
        tested_server.signal_stop_all()

    for mock_client in tested_server.clients:
        mock_client.send.assert_called_once_with(expected_message)
