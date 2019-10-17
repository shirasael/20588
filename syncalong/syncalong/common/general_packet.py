from scapy.compat import raw
from scapy.fields import IntEnumField, FieldLenField, ConditionalField, PacketField
from scapy.packet import Packet, bind_layers, Padding

from syncalong.common.signal_packet import SignalPacket, STOP_SIGNAL
from syncalong.common.file_sync_packet import FileSyncPacket, WHO_HAS

all_layers = [SignalPacket, FileSyncPacket]
layers_dict = {}

for idx, layer in enumerate(all_layers):
    bind_layers(layer, Padding)
    layers_dict.update({idx: layer.__name__})


def condition(layer_cls):
    return ConditionalField(PacketField(layer_cls._name, layer_cls(), layer_cls),
                            lambda pkt: pkt.layer_type == all_layers.index(layer_cls))


class GeneralPacket(Packet):
    name = "GeneralPacket"
    fields_desc = [
        IntEnumField("layer_type", 1, layers_dict),
        condition(SignalPacket),
        condition(FileSyncPacket),
    ]


def handle_packet(pkt: GeneralPacket, type_handlers):
    layer_type = all_layers[pkt.layer_type]
    handler = type_handlers[layer_type]
    inner_pkt = pkt[layer_type]
    return handler(inner_pkt)


def generate_packet(pkt):
    gp = GeneralPacket(
        layer_type=pkt.__class__.__name__,
    )
    gp.__setattr__(pkt._name, pkt)
    return gp


if __name__ == "__main__":
    sp = SignalPacket(signal=STOP_SIGNAL,
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
