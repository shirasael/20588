import socket
import _socket
from typing import List

from scapy.compat import raw
from common.general_packet import GeneralPacket, generate_packet


def int_to_bytes(x: int) -> bytes:
    return x.to_bytes(4, 'big')


def int_from_bytes(xbytes: bytes) -> int:
    return int.from_bytes(xbytes, 'big')


class LengthSocket(socket.socket):
    """
    A socket that is designed to send / receive messages by length.
    Every message sent by this socket is preceded by its length, and every message read by this socket is expected
    to be in the format of [length|data] where data's length is as specified.

    Length packet also offers integration with packets used by server / clients in this program, and is responsible
    for building the packets properly before sending them.
    """
    def send(self, data: bytes, flags: int = ...) -> int:
        """
        Send the given bytes, preceding their length. Flags are ignored.
        :param data: The data to be sent.
        :param flags: Ignored.
        :return: Total amount of bytes sent (data length bytes + data length)
        """
        sent_len = super().send(int_to_bytes(len(data)))
        sent_data = super().send(data)
        return sent_len + sent_data

    def send_packet(self, packet):
        """
        Send a single packet (alongside its length).
        A packet might be of type GeneralPacket, of a specific custom packet which is part of this program's
        protocol (to be wrapped by GeneralPacket), or simple bytes.

        If bytes are passed, they'll be sent as-is.
        If a GeneralPacket is passed, it'll be built and sent.
        If a custom packet is passed, it'll be wrapped with GeneralPacket, and then built and sent.

        :param packet: The packet (or bytes) to be sent.
        :return: Total amount of bytes sent.
        """
        if isinstance(packet, bytes):
            return self.send(packet)
        packet_to_send = packet
        if not isinstance(packet_to_send, GeneralPacket):
            packet_to_send = generate_packet(packet)
        return self.send(raw(packet_to_send))

    def recv(self, bufsize: int = -1, flags: int = ...) -> bytes:
        """
        Receive bytes from socket.
        If bufsize is specified and is >= 0, the specific amount of bytes will be read.
        Otherwise, the socket will first recv 4 bytes representing the message length, and then read it.
        Receiving i done at once, for the entire buffer size (no split).

        The return value is the data that was received (without length bytes).

        :param bufsize: The size of the data to recv, or -1 in order to receive a message with size specified.
        :param flags: Ignored.
        :return: The data received from the socket.
        """
        if bufsize >= 0:
            return super().recv(bufsize)
        else:
            length = int_from_bytes(super().recv(4))
            return super().recv(int(length))

    def accept(self):
        """
        Accept a new clients and return it as a LengthSocket.
        :return: A connection that was made to the socket.
        :rtype: LengthSocket
        """
        conn, addr = super().accept()
        fd = _socket.dup(conn.fileno())
        sock = LengthSocket(self.family, self.type, self.proto, fileno=fd)
        return sock, addr

    def send_all(self, packets):
        """
        Send all the given packets.
        :param packets: List of packets to be sent.
        """
        for packet in packets:
            self.send_packet(packet)

    def __repr__(self):
        addr, port = self.getsockname()
        return f"<LengthSocket {addr}:{port}>"


def send_to_all(sockets: List[LengthSocket], packets):
    """
    Send all the given packets to all the given sockets.
    If there was a failure while trying to send a packet to a client, this client will not be receiving any more
    of the packets that are sent.

    :param sockets: Sockets to send the packets to.
    :param packets: Packets to be sent to all clients.
    """
    sending_sockets = [s for s in sockets]
    for packet in packets:
        for s in sending_sockets:
            try:
                s.send_packet(packet)
            except (Exception, socket.error) as e:
                print(f"Could not send packets to {s}: {e}")
                print(f"Stopping transmit to {s}")
                sending_sockets.remove(s)
