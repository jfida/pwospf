from mininet.topo import Topo

class StaticLinearSwitchTopo(Topo):
    class LinearTopo( Topo ):
    "Linear topology of k switches, with n hosts per switch."

    def build( self, k=2, n=1, **_opts):
        """k: number of switches
           n: number of hosts per switch"""
        self.k = k
        self.n = n

        if n == 1:
            genHostName = lambda i, j: 'h%s' % i
        else:
            genHostName = lambda i, j: 'h%ss%d' % ( j, i )

        lastSwitch = None
        for i in irange( 1, k ):
            # Add switch
            switch = self.addSwitch( 's%s' % i )
            # Add hosts to switch
            for j in irange( 1, n ):
                host = self.addHost( genHostName( i, j ) )
                self.addLink( host, switch )
            # Connect switch to previous
            if lastSwitch:
                self.addLink( switch, lastSwitch )
            lastSwitch = switch

class SingleSwitchTopo(Topo):
    def __init__(self, n, **opts):
        Topo.__init__(self, **opts)

        switch = self.addSwitch('s1')

        for i in xrange(1, n+1):
            host = self.addHost('h%d' % i,
                                ip = "10.0.0.%d" % i,
                                mac = '00:00:00:00:00:%02x' % i)
            self.addLink(host, switch, port2=i)
