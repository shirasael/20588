from scapy.fields import ByteEnumField, LongField, FieldLenField, FieldListField, StrLenField
from scapy.packet import Packet

PLAY_SIGNAL = 1
STOP_SIGNAL = 2

commands = {PLAY_SIGNAL: "PLAY", STOP_SIGNAL: "STOP"}


class Param(Packet):
    fields_desc = [FieldLenField("param_name_len", None, length_of="param_name"),
                   StrLenField("param_name", 0),
                   FieldLenField("param_len", None, length_of="param_data"),
                   StrLenField("param_data", 0)]


class SignalPacket(Packet):
    name = "SignalPacket"
    fields_desc = [ByteEnumField("command", len(commands), commands),
                   LongField("send_timestamp", 0),
                   FieldLenField("params_len", None, count_of="params"),
                   FieldListField("params", [], Param,
                                  count_from=lambda pkt: pkt.params_len)]
