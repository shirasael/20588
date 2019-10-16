import time

import mock

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
    tested_server.stop()
    assert tested_server.clients == {
        Entity("1.1.1.1", 12345): accept_mock_values[0][0],
        Entity("2.2.2.2", 23456): accept_mock_values[1][0]
    }
