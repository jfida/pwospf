from scapy.all import *
import sys, os

TYPE_MYTUNNEL = 0x1212
TYPE_IPV4 = 0x080a
TYPE_OSPF = 89


class PWOSPFHeader(Packet):
    name = "pwospf header"
    fields_desc = [
        ByteField("version", 0),
        ByteEnumField("type", 2, {1: "HELLO", 4: "LSU"}),
        ShortField("packet_length", 0),
        IntField("router_ID", 0),
        IntField("area_ID", 0),
        ShortField("checksum", 0),
        ShortField("autype", 0),
        LongField("autentication", 0)
    ]


class PWOSPFHello(Packet):
    name = "pwospf hello"
    fields_desc = [
        IntField("network_mask", 0),
        ShortField("hello_int", 0),
        ShortField("padding", 0)
    ]


class PWOSPFLsu(Packet):
    name = "pwospf lsu"
    fields_desc = [
        ByteField("version", 0),
        ByteField("type", 0),
        ShortField("packet_length", 0),
        IntField("router_ID", 0),
        IntField("area_ID", 0),
        ShortField("checksum", 0),
        ShortField("autype", 0),
        LongField("autentication", 0),
        ShortField("sequence", 0),
        ShortField("ttl", 0),
        IntField("adv_number", 0),
        IntField("adv", 0)
    ]


bind_layers(IP, PWOSPFHeader, proto=TYPE_OSPF)
bind_layers(PWOSPFHeader, PWOSPFHello, type=1)
bind_layers(PWOSPFHeader, PWOSPFLsu, type=4)
