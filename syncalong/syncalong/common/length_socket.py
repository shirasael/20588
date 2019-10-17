import socket
import _socket

from scapy.compat import raw
from scapy.packet import Packet

from common.general_packet import GeneralPacket, generate_packet


def int_to_bytes(x: int) -> bytes:
    return x.to_bytes(4, 'big')


def int_from_bytes(xbytes: bytes) -> int:
    return int.from_bytes(xbytes, 'big')


class LengthSocket(socket.socket):

    def send(self, data: bytes, flags: int = ...) -> int:
        sent_len = super().send(int_to_bytes(len(data)))
        sent_data = super().send(data)
        return sent_len + sent_data

    def send_packet(self, packet):
        if isinstance(packet, bytes):
            return self.send(packet)
        packet_to_send = packet
        if not isinstance(packet_to_send, GeneralPacket):
            packet_to_send = generate_packet(packet)
        return self.send(raw(packet_to_send))

    def recv(self, bufsize: int = -1, flags: int = ...) -> bytes:
        if bufsize >= 0:
            return super().recv(bufsize)
        else:
            length = int_from_bytes(super().recv(4))
            return super().recv(int(length))

    def accept(self):
        conn, addr = super().accept()
        fd = _socket.dup(conn.fileno())
        sock = LengthSocket(self.family, self.type, self.proto, fileno=fd)
        return sock, addr


