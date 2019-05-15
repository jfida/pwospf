# noinspection PyUnresolvedReferences
from mininet.topo import Topo


# Topology
#        c1       c2
#        |        |
#        1:       1:
# h1---2:s1:3---2:s2:3---h2
#        :4
#        |
#        :2
# c3---1:s3:3--h3

class MyTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)

        # hosts
        h1 = self.addHost('h1', ip="10.0.0.1", mac="00:00:00:00:00:01")
        h2 = self.addHost('h2', ip="10.0.0.2", mac="00:00:00:00:00:02")
        h3 = self.addHost('h3', ip="10.0.0.5", mac="00:00:00:00:00:03")

        # switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # controllers
        c1 = self.addHost('c1', ip="10.0.0.3", mac="00:00:00:00:01:01")
        c2 = self.addHost('c2', ip="10.0.0.4", mac="00:00:00:00:01:02")
        c3 = self.addHost('c3', ip="10.0.0.6", mac="00:00:00:00:01:03")

        # links
        self.addLink(s1, s2, port1=3, port2=2)
        self.addLink(s1, s3, port1=4, port2=2)
        self.addLink(c1, s1, port2=1)
        self.addLink(c2, s2, port2=1)
        self.addLink(c3, s3, port2=1)
        self.addLink(h1, s1, port2=2)
        self.addLink(h2, s2, port2=3)
        self.addLink(h3, s3, port2=3)
