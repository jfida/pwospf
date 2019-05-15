from threading import Thread, Event
from scapy.all import sendp
# noinspection PyUnresolvedReferences
from scapy.all import Packet, Ether, IP
from pwospf_pkt import PWOSPFHeader, PWOSPFHello, PWOSPFLsu
from async_sniff import sniff
from cpu_metadata import CPUMetadata
import time

ALLSPFRouters = "224.0.0.5"
MGID = 1
# ALLSPFRouters = "10.0.0.2"


class PWOSPFController(Thread):
    def __init__(self, sw, node, rid, area_id, mask, start_wait=0.5):
        super(PWOSPFController, self).__init__()
        self.sw = sw
        self.rid = rid
        self.area_id = area_id
        self.mask = mask
        self.start_wait = start_wait
        self.iface = sw.intfs[1].name
        self.port_for_mac = {}
        self.stop_event = Event()
        self.node = node
        self.db = {}
        self.hello_pkt = (Ether(dst="ff:ff:ff:ff:ff:ff")
                          / IP(src=sw.IP(), dst=ALLSPFRouters)
                          / PWOSPFHeader(type=1, packet_length=32, router_ID=self.rid, area_ID=self.area_id)
                          / PWOSPFHello(network_mask=self.mask)
                          )
        self.multicast_setup()

    def add_routing_entry(self, port, host):
        self.sw.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                                 match_fields={'hdr.ipv4.dstAddr': [host.IP(), 32]},
                                 action_name='MyIngress.ipv4_forward',
                                 action_params={'dstAddr': host.MAC(),
                                                'port': port})

    def add_mac_addr(self, mac, port):
        # Don't re-add the mac-port mapping if we already have it:
        if mac in self.port_for_mac: return

        self.sw.insertTableEntry(table_name='MyIngress.fwd_l2',
                                 match_fields={'hdr.ethernet.dstAddr': [mac]},
                                 action_name='MyIngress.set_egr',
                                 action_params={'port': port})
        self.port_for_mac[mac] = port

    def handle_pkt(self, pkt):
        pkt.show2()
        print(pkt.haslayer(IP))
        # assert CPUMetadata in pkt, "Should only receive packets from switch with special header"
        return

    def send_hello(self):
        self.send(self.hello_pkt)

    def send(self, *args, **override_kwargs):
        pkt = args[0]
        # assert CPUMetadata in pkt, "Controller must send packets with special header"
        # pkt[CPUMetadata].fromCpu = 1
        kwargs = dict(iface=self.iface, verbose=False)
        kwargs.update(override_kwargs)
        sendp(*args, **kwargs)

    def run(self):
        sniff(iface=self.iface, prn=self.handle_pkt, stop_event=self.stop_event)

    def start(self, *args, **kwargs):
        super(PWOSPFController, self).start()
        time.sleep(self.start_wait)

    def join(self, *args, **kwargs):
        self.stop_event.set()
        super(PWOSPFController, self).join(*args, **kwargs)

    def multicast_setup(self):
        self.sw.insertTableEntry(
            table_name="MyIngress.ipv4_lpm",
            match_fields={"hdr.ipv4.dstAddr": [ALLSPFRouters, 32]},
            action_name="MyIngress.set_mgid",
            action_params={"mgid": MGID},
        )
        self.sw.addMulticastGroup(mgid=MGID, ports=range(2, len(self.sw.ports)))
