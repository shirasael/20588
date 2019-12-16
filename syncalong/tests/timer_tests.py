import pytest

import syncalong.client.timer
import datetime

REMOTE_TIME_DIFF = datetime.timedelta(seconds=10)


def stub_get_remote_time(*args, **kwargs):
    return datetime.datetime.now() - REMOTE_TIME_DIFF


syncalong.client.timer.get_remote_time = stub_get_remote_time


@pytest.mark.parametrize("expected_actual_wait_range, server_send_secs",
                         [
                             (
                                     (datetime.timedelta(seconds=1, microseconds=500),
                                      datetime.timedelta(seconds=2, microseconds=500)),
                                     1
                             ),
                             (
                                     (datetime.timedelta(seconds=0, microseconds=0),
                                      datetime.timedelta(seconds=0, microseconds=500)),
                                     4
                             )
                         ])
def test_wait_for_remote(expected_actual_wait_range, server_send_secs):
    """
    Server request sent at time X - server_send_secs, and received at X.
    Wait time should be 3 seconds from send on server.
    """
    remote_wait_seconds = 3
    remote_start_time = datetime.datetime.now() - (REMOTE_TIME_DIFF + datetime.timedelta(seconds=server_send_secs))
    start_milli_secs = datetime.datetime.now()
    client.timer.wait_for_remote_time(remote_start_time, remote_wait_seconds, 'dummy.ntp.server')
    end_milli_secs = datetime.datetime.now()
    assert expected_actual_wait_range[0] <= (end_milli_secs - start_milli_secs) <= expected_actual_wait_range[1]
