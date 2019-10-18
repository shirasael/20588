from scapy.fields import FieldLenField, StrField, IntField, IntEnumField, IEEEFloatField, IEEEDoubleField
from scapy.packet import Packet

DEFAULT_WAIT_SECONDS = 5

PLAY_SIGNAL = 1
STOP_SIGNAL = 2

commands = {PLAY_SIGNAL: "PLAY", STOP_SIGNAL: "STOP"}


class SignalPacket(Packet):
    name = "signal_packet"
    fields_desc = [IntEnumField("signal", 1, commands),
                   IEEEDoubleField("send_timestamp", 0),
                   IntField("wait_seconds", DEFAULT_WAIT_SECONDS),
                   FieldLenField("music_file_name_len", None, length_of="music_file_name"),
                   StrField("music_file_name", "")]

    def __eq__(self, other):
        return self.signal == other.signal \
               and self.send_timestamp == other.send_timestamp \
               and self.wait_seconds == other.wait_seconds \
               and self.music_file_name == other.music_file_name
