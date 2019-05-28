# noinspection PyUnresolvedReferences
from p4app import P4Mininet

from controller import PWOSPFController
from my_topo import MyTopo
import time

topo = MyTopo()
net = P4Mininet(program='pwospfswitch.p4', topo=topo)
net.start()

h1, h2, h3 = net.get('h1'), net.get('h2'), net.get('h3')
s1, s2, s3 = net.get('s1'), net.get('s2'), net.get('s3')
c1, c2, c3 = net.get('c1'), net.get('c2'), net.get('c3')

# Start the PWOSPF controllers
cpu1 = PWOSPFController(sw=s1, node=c1, rid=1, area_id=1, mask=0xFFFFFFFF)
cpu2 = PWOSPFController(sw=s2, node=c2, rid=2, area_id=1, mask=0xFFFFFFFF)
cpu3 = PWOSPFController(sw=s3, node=c3, rid=3, area_id=1, mask=0xFFFFFFFF)
cpu1.start()
cpu2.start()
cpu3.start()

# Populate IPv4 forwarding table
# cpu1.add_routing_entry(2, h1.IP())
# cpu1.add_routing_entry(3, h2.IP())
# cpu1.add_routing_entry(4, h3.IP())
#
# cpu2.add_routing_entry(2, h1.IP())
# cpu2.add_routing_entry(3, h2.IP())  # hardcoded controller rerouting to port 1, change port back to 3 when done
# cpu2.add_routing_entry(2, h3.IP())
#
# cpu3.add_routing_entry(2, h1.IP())
# cpu3.add_routing_entry(2, h2.IP())
# cpu3.add_routing_entry(3, h3.IP())

# Start the server with some key-values
# net.ping([h1, h2])
# net.ping([h1, h3])
# net.ping([h2, h3])

# Send test PWOSPF HELLO pkt
# cpu1.send_hello()
# cpu2.send_hello()
# cpu3.send_hello()

# cpu3.add_routing_entry(4, "10.0.1.3")

# print("1:", cpu1.routing)
# print("2:", cpu2.routing)
# print("3:", cpu3.routing)

time.sleep(5)

cpu1.stop()
cpu2.stop()
cpu3.stop()

cpu1.join()
cpu2.join()
cpu3.join()

exit(0)
