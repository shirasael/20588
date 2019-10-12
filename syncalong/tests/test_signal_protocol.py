from common.signal_protocol import *


def test_simple_params_extract():
    dummy_packet = SignalPacket(command=PLAY_SIGNAL, send_timestamp=5,
                                params=[Param(param_name="one", param_data="heyy"),
                                        Param(param_name="two", param_data="yoo")])
    assert extract_params(dummy_packet) == {"one": "heyy", "two": "yoo"}


def test_no_params_extract():
    dummy_packet = SignalPacket(command=PLAY_SIGNAL, send_timestamp=5)
    assert extract_params(dummy_packet) == {}
