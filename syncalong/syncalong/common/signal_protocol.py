from scapy.fields import FieldLenField, PacketListField, StrField, IntField, IntEnumField, IEEEFloatField, StrLenField
from scapy.packet import Packet, Raw

DEFAULT_WAIT_SECONDS = 3


PLAY_SIGNAL = 1
STOP_SIGNAL = 2

commands = {PLAY_SIGNAL: "PLAY", STOP_SIGNAL: "STOP"}


class SignalPacket(Packet):
    name = "SignalPacket"
    fields_desc = [IntEnumField("signal", 1, commands),
                   IEEEFloatField("send_timestamp", 0),
                   IntField("wait_seconds", DEFAULT_WAIT_SECONDS),
                   FieldLenField("music_file_path_len", None, length_of="music_file_path"),
                   StrField("music_file_path", None)]


