from scapy.compat import raw
from scapy.fields import IntEnumField, ConditionalField, PacketField
from scapy.packet import Packet, bind_layers, Padding

from syncalong.common.signal_packet import SignalPacket
from syncalong.common.file_sync_packet import FileSyncPacket
from syncalong.common.data_packet import DataPacket

# All of the possible packets in the program.
all_layers = [SignalPacket, FileSyncPacket, DataPacket]

layers_dict = {}

for idx, layer in enumerate(all_layers):
    bind_layers(layer, Padding)
    layers_dict.update({idx: layer.__name__})


def condition(layer_cls) -> ConditionalField:
    """
    Create a conditional layer field. the layer must be present in `all_layers`.
    :param layer_cls: Layer class to create conditional field for.
    :return: Conditional field representing the given layer.
    """
    return ConditionalField(PacketField(layer_cls._name, layer_cls(), layer_cls),
                            lambda pkt: pkt.layer_type == all_layers.index(layer_cls))


class GeneralPacket(Packet):
    """
    Packet that holds messages of specific types.
    This packet was made in order to make communication with the multiple protocols easy, and handle different requests
    in an agnostic way (without checking types all the time).
    """
    name = "GeneralPacket"
    fields_desc = [
        IntEnumField("layer_type", 1, layers_dict),
        condition(SignalPacket),
        condition(FileSyncPacket),
        condition(DataPacket),
    ]


def handle_packet(pkt: GeneralPacket, type_handlers):
    """
    Handle a general packet using the given handlers.
    The handlers should map a packet type (in `all_layers`) to a function, that will take in the packet of this type
    found in the inner layer of the given GeneralPacket.

    :param pkt: A GeneralPacket to be handled.
    :param type_handlers: dictionary mapping layer type to its handler function.
    :return: Return value of handler function.
    """
    layer_type = all_layers[pkt.layer_type]
    handler = type_handlers[layer_type]
    inner_pkt = pkt[layer_type]
    return handler(inner_pkt)


def generate_packet(pkt) -> GeneralPacket:
    """
    Wrap a wiven packet with a GeneralPacket.
    :param pkt: Packet to be wrapped (type must be one of the types in `all_layers`)
    :return: GeneralPacket with the given packet as an inner field.
    """
    gp = GeneralPacket(
        layer_type=pkt.__class__.__name__,
    )
    gp.__setattr__(pkt._name, pkt)
    return gp


if __name__ == "__main__":
    print("Testing general packet")

    sp = SignalPacket(signal=0,
                      send_timestamp=123,
                      wait_seconds=4,
                      music_file_name="")

    g = generate_packet(sp)

    print(g.show())
    r = raw(g)
    print(r)
    gg = GeneralPacket(r)
    print(gg.show())
    print(gg.layer_type)

    print("-----")

    handle_packet(gg, {
        SignalPacket: lambda pkt: print(pkt.send_timestamp),
        FileSyncPacket: lambda pkt: print(pkt.file_name)
    })
