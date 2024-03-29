import os
from typing import List

from scapy.fields import IntEnumField, FieldLenField, StrField, IntField
from scapy.packet import Packet

MISSING = 0
HAVE = 1
WHO_HAS = 2
FILE_SEND = 3

message_types = {WHO_HAS: "WHO_HAS", HAVE: "HAVE", MISSING: "MISSING", FILE_SEND: "FILE_SEND"}


class FileSyncPacket(Packet):
    name = "file_sync_packet"
    fields_desc = [
        IntEnumField("message_type", 1, message_types),
        IntField("file_size", 0),
        FieldLenField("file_name_len", None, length_of="file_name"),
        StrField("file_name", ""),
    ]


def who_has_packet(file_path: str) -> FileSyncPacket:
    return FileSyncPacket(message_type=WHO_HAS,
                          file_name=os.path.basename(file_path),
                          file_size=os.path.getsize(file_path))


def who_has_answer_packet(file_path: str, file_size: int) -> FileSyncPacket:
    response = HAVE
    if not os.path.exists(file_path) or os.path.getsize(file_path) != file_size:
        response = MISSING
    print("Who has response: {}".format(message_types[response]))
    return FileSyncPacket(message_type=response)


def send_file_packets(file_path: str) -> List[FileSyncPacket]:
    packets = [FileSyncPacket(message_type=FILE_SEND,
                              file_name=os.path.basename(file_path),
                              file_size=os.path.getsize(file_path))]
    with open(file_path, 'rb') as file_to_send:
        data = file_to_send.read()
        packets.append(data)
    return packets
