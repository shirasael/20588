from scapy.fields import ByteEnumField, LongField, FieldLenField, PacketListField, StrField
from scapy.packet import Packet

PLAY_SIGNAL = 1
STOP_SIGNAL = 2

commands = {PLAY_SIGNAL: "PLAY", STOP_SIGNAL: "STOP"}


class Param(Packet):
    fields_desc = [FieldLenField("param_name_len", None, length_of="param_name"),
                   StrField("param_name", None, fmt="H"),
                   FieldLenField("param_len", None, length_of="param_data"),
                   StrField("param_data", None, fmt="H")]


class SignalPacket(Packet):
    name = "SignalPacket"
    fields_desc = [ByteEnumField("command", len(commands), commands),
                   LongField("send_timestamp", 0),
                   FieldLenField("params_len", None, count_of="params"),
                   PacketListField("params", [], Param,
                                   count_from=lambda pkt: pkt.params_len)]


def extract_params(signal_packet: SignalPacket):
    return {param.param_name.decode("utf-8"): param.param_data.decode("utf-8") for param in signal_packet.params}

