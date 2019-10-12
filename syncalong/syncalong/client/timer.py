import datetime
import time

from ntplib import NTPClient


def wait_for_remote_time(remote_start_time: datetime.datetime,
                         wait_time_seconds: int,
                         ntp_server,
                         ntp_port=123):
    """
    Wait the given amount of seconds, starting from the given remote time. The function returns when the remote
    time is exactly remote_start_time + wait_time_seconds.
    """
    wait_delta = datetime.timedelta(seconds=wait_time_seconds)
    target_time = remote_start_time + wait_delta
    current_remote_time = get_remote_time(ntp_server, ntp_port)
    print(current_remote_time, target_time)
    if target_time > current_remote_time:
        time.sleep((target_time - current_remote_time).seconds)


def get_remote_time(ntp_server, ntp_port=123):
    ntp_client = NTPClient()
    result = ntp_client.request(ntp_server, port=ntp_port)
    return datetime.datetime.fromtimestamp(result.tx_time)
