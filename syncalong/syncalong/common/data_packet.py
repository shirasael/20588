import os

from scapy.fields import IntEnumField, FieldLenField, StrField, IntField
from scapy.packet import Packet


class DataPacket(Packet):
    name = "data_packet"
    fields_desc = [
        FieldLenField("data_len", None, length_of="data"),
        StrField("data", ""),
    ]