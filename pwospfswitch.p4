/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4  = 0x800;
const bit<16> TYPE_META  = 0x80a;
const bit<8>  TYPE_UDP   = 3;
const bit<8>  TYPE_OSPF  = 89;
const bit<8>  TYPE_HELLO = 1;
const bit<8>  TYPE_LSU   = 4;

const bit<9> CPU_PORT = 1;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header cpu_metadata_t {
    bit<8>  fromCpu;
    bit<16> origEtherType;
    bit<16> srcPort;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   checksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header udp_t {
    bit<16>   srcPort;
    bit<16>   dstPort;
    bit<16>   totalLen;
    bit<16>   checksum;
}

header ospf_t {
    bit<8>      version;
    bit<8>      type;
    bit<16>     packet_length;
    bit<32>     router_ID;
    bit<32>     area_ID;
    bit<16>     checksum;
    bit<16>     autype;
    bit<64>     auth;
}

header hello_t {
    bit<32>     network_mask;
    bit<16>     hello_int;
    bit<16>     padding;
}

header lsu_t {
    bit<8>      version;
    bit<8>      type;
    bit<16>     packet_length;
    bit<32>     router_ID;
    bit<32>     area_ID;
    bit<16>     checksum;
    bit<16>     autype;
    bit<64>     autentication;
    bit<16>     sequence;
    bit<16>     ttl;
    bit<32>     adv_number;
    bit<32>     adv;
}

struct metadata {
    /* empty */
}

struct headers {
    ethernet_t      ethernet;
    cpu_metadata_t  cpu_metadata;
    ipv4_t          ipv4;
    udp_t           udp;
    ospf_t          ospf;
    hello_t         hello;
    lsu_t           lsu;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            TYPE_META: parse_cpu_metadata;
            default: accept;
        }
    }

    state parse_cpu_metadata {
        packet.extract(hdr.cpu_metadata);
        transition select(hdr.cpu_metadata.origEtherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            TYPE_OSPF: parse_ospf;
            TYPE_UDP: parse_udp;
            default: accept;
        }
    }

    state parse_udp {
        packet.extract(hdr.udp);
        transition accept;
    }

    state parse_ospf {
        packet.extract(hdr.ospf);
        transition select(hdr.ospf.type) {
            TYPE_HELLO: parse_hello;
            TYPE_LSU: parse_lsu;
            default: accept;
        }
    }

    state parse_hello {
        packet.extract(hdr.hello);
        transition accept;
    }

    state parse_lsu {
        packet.extract(hdr.lsu);
        transition accept;
    }

}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    action drop() {
        mark_to_drop();
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action cpu_meta_encap() {
        hdr.cpu_metadata.setValid();
        hdr.cpu_metadata.origEtherType = hdr.ethernet.etherType;
        hdr.cpu_metadata.srcPort = (bit<16>) standard_metadata.ingress_port;
        hdr.ethernet.etherType = TYPE_META;
    }

    action cpu_meta_decap() {
        hdr.ethernet.etherType = hdr.cpu_metadata.origEtherType;
        hdr.cpu_metadata.setInvalid();
    }

    action send_to_cpu() {
        cpu_meta_encap();
        standard_metadata.egress_spec = CPU_PORT;
    }

    action set_mgid(bit<16> mgid) {
        standard_metadata.mcast_grp = mgid;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            set_mgid;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    apply {

        if (standard_metadata.ingress_port == CPU_PORT)
            cpu_meta_decap();

        if (hdr.ospf.isValid() && standard_metadata.ingress_port != CPU_PORT)
            send_to_cpu();
        else if (hdr.ipv4.isValid() && hdr.ipv4.ttl > 0)
            ipv4_lpm.apply();
        else
            drop();
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

    action override_destination(macAddr_t macAddr, ip4Addr_t ipAddr) {
        hdr.ethernet.dstAddr = macAddr;
        hdr.ipv4.dstAddr = ipAddr;
    }

    action drop() {
        mark_to_drop();
    }

    table override {
        key = { standard_metadata.egress_port: exact; }
        actions = {
            override_destination;
            drop;
            NoAction;
        }
        size = 256;
        default_action = NoAction();
    }


    apply {
        if (hdr.ipv4.isValid()) override.apply();
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply {
        update_checksum(
        hdr.ipv4.isValid(),
        {
            hdr.ipv4.version,
            hdr.ipv4.ihl,
            hdr.ipv4.diffserv,
            hdr.ipv4.totalLen,
            hdr.ipv4.identification,
            hdr.ipv4.flags,
            hdr.ipv4.fragOffset,
            hdr.ipv4.ttl,
            hdr.ipv4.protocol,
            hdr.ipv4.srcAddr,
            hdr.ipv4.dstAddr
        },
        hdr.ipv4.checksum,
        HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.cpu_metadata);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.ospf);
        packet.emit(hdr.hello);
        packet.emit(hdr.lsu);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;