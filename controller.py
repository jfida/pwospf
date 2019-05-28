from threading import Thread, Event, Timer

from scapy.all import sendp
# noinspection PyUnresolvedReferences
from scapy.all import Packet, Ether, IP
from pwospf_pkt import PWOSPFHeader, PWOSPFHello, PWOSPFLsu
from async_sniff import sniff
from cpu_metadata import CPUMetadata
import time
import threading

ALLSPFRouters = "224.0.0.5"
MGID = 1


class PWOSPFController(Thread):
    def __init__(self, sw, node, rid, area_id, mask, start_wait=0.5):
        super(PWOSPFController, self).__init__()
        self.halt = False
        self.listen_thread = None
        self.hello_thread = None
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
                          / CPUMetadata(fromCpu=1, origEtherType=0x800)
                          / IP(src=node.IP(), dst=ALLSPFRouters)
                          / PWOSPFHeader(type=1, packet_length=32, router_ID=self.rid, area_ID=self.area_id)
                          / PWOSPFHello(network_mask=self.mask)
                          )
        self.multicast_setup()
        self.routing = {}
        self.V = []
        self.E = []

    def add_routing_entry(self, port, ip):
        self.sw.insertTableEntry(table_name='MyIngress.ipv4_lpm',
                                 match_fields={'hdr.ipv4.dstAddr': [ip, 32]},
                                 action_name='MyIngress.ipv4_forward',
                                 action_params={'dstAddr': "ff:ff:ff:ff:ff:ff",
                                                'port': port})

    def send_hello(self):
        print(self.halt)
        if self.halt:
            exit(0)
        self.send(self.hello_pkt)

    def send(self, *args, **override_kwargs):
        pkt = args[0]
        # assert CPUMetadata in pkt, "Controller must send packets with special header"
        # pkt[CPUMetadata].fromCpu = 1
        kwargs = dict(iface=self.iface, verbose=False)
        kwargs.update(override_kwargs)
        sendp(*args, **kwargs)

    def handle_pkt(self, pkt):
        if PWOSPFHeader in pkt and pkt[CPUMetadata].srcPort != 0:
            if pkt[PWOSPFHeader].type == 1:
                ip_src = str(pkt[IP].src)
                node = (ip_src, pkt[CPUMetadata].srcPort)
                if node not in self.V:
                    self.V.append(node)
                edge = ((self.node.IP(), 0), node)
                if edge not in self.E:
                    self.E.append(edge)
                self.recompute_routing()
                self.update_routing_entries()
                # print(self.V)
                # print(self.E)
                # if node not in self.routing:
                #     self.recompute_routing()
                #     print(self.routing)
                #     self.add_routing_entry(node[0], node[1], pkt[CPUMetadata].srcPort)
                #     print(self.routing)
        # pkt.show2()

    def run(self):
        self.listen_thread = threading.Thread(target=self.sniff)
        self.hello_thread = threading.Thread(target=self.hola)
        self.listen_thread.start()
        self.hello_thread.start()

    def sniff(self):
        sniff(iface=self.iface, prn=self.handle_pkt, stop_event=self.stop_event)

    def hola(self):
        self.send_hello()
        Timer(15, self.send_hello).start()

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

    def recompute_routing(self):
        prev = {}

        # init prev maps
        for v in self.V:
            prev[v] = {}
            for w in self.V:
                prev[v][w] = None
        next = prev

        # compute prev dict
        for v in prev:
            front, visit = [v], [v]
            while front:
                w = front.pop(0)
                for x in [edge[1 - edge.index(w)] for edge in self.E if w in edge]:
                    if x not in visit:
                        visit.append(x)
                        prev[v][x] = w
                        front.append(x)

        # compute next dict
        for v in self.V:
            for w in self.V:
                if prev[v][w] == w:
                    next[w][v] = w
                else:
                    next[w][v] = prev[v][w]

        self.routing = next

    def update_routing_entries(self):
        me = (self.node.IP(), 0)
        for dst in self.routing:
            if dst != self.node.IP() and self.routing.get(dst).get(me) is not None:
                out_port = self.routing.get(dst).get(me)[1]
                print("Switch " + str(self.node) + " added ipv4 entry: (IP: " + dst[0] + ", PORT: " + str(out_port) + ")")
                self.add_routing_entry(out_port, dst[0])
                pass

    def stop(self):
        self.halt = True
        self.stop_event.set()
        self.listen_thread.join()
        self.hello_thread.join()
        exit(0)

