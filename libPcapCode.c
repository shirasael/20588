#include <pcap.h>
#include <stdio.h> 
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/if_ether.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

#define ETHERTYPE_IP 0x0800 /* IP */
#define ETHERTYPE_ARP 0x0806 /* Address resolution */ 


pcap_t* openGoLiveAndSetFilter(char* filter) {
	char *dev; /* name of the device to use */
	pcap_t* descr; /* pointer to device descriptor */
	const u_char *packet; /* pointer to packet */
	bpf_u_int32 maskp; /* subnet mask */
	bpf_u_int32 netp; /* ip */
	char errbuf[PCAP_ERRBUF_SIZE];
	struct bpf_program fp;

	/* ask pcap to find a valid device to sniff */
	dev = pcap_lookupdev(errbuf);
	if(dev == NULL) {
		printf("%s\n",errbuf);
		exit(1);
	}
	printf("DEV: %s\n",dev);
	
	/* ask pcap for the network address and mask of the device */
	pcap_lookupnet(dev,&netp,&maskp,errbuf);
	descr = pcap_open_live(dev,BUFSIZ, 0, -1,errbuf);

	/* BUFSIZ is max packet size to capture, 0 is promiscous, -1 means don’t wait for read to time out. */
	if(descr == NULL) {
		printf("pcap_open_live(): %s\n",errbuf);
		exit(1);
	}

	if (pcap_compile(descr,&fp,filter,0,netp) == -1) {
		fprintf(stderr,"Error calling pcap_compilen");
		exit(1);
	}
	if (pcap_setfilter(descr,&fp) == -1) {
		fprintf(stderr,"Error setting filtern");
		exit(1);
	} 

	return descr;
}

void sniffOnePacket(int argc, char **argv) {
	struct pcap_pkthdr hdr; /* struct: packet header */
	pcap_t* descr; /* pointer to device descriptor */
	const u_char *packet; /* pointer to packet */

	descr = openGoLiveAndSetFilter(NULL);

	packet = pcap_next(descr, &hdr);

	if (packet == NULL) {
		printf("It got away!\n");
	} else {
		printf("one lonely packet.\n");
	}
}

void my_callback(u_char *useless,const struct pcap_pkthdr* pkthdr,const u_char* packet) { 
	printf("Handling packet of type ");
	struct ether_header *eth_header;
	/* The packet is larger than the ether_header struct,
	but we just want to look at the first part of the packet
	that contains the header. We force the compiler
	to treat the pointer to the packet as just a pointer
	to the ether_header. The data payload of the packet comes
	after the headers. Different packet types have different header
	lengths though, but the ethernet header is always the same (14 bytes) */
	eth_header = (struct ether_header *) packet;

	if (ntohs(eth_header->ether_type) == ETHERTYPE_IP) {
		printf("IP\n");
	} else  if (ntohs(eth_header->ether_type) == ETHERTYPE_ARP) {
		printf("ARP\n");
	} else  if (ntohs(eth_header->ether_type) == ETHERTYPE_REVARP) {
		printf("Reverse ARP\n");
	}
}

void snifferLoop(int argc, char **argv) {
	pcap_t* descr; /* pointer to device descriptor */
	char* filter = NULL;
	if (argc > 1) {
		filter = argv[1];
		printf("Filter: %s\n", filter);
	}
	descr = openGoLiveAndSetFilter(filter);
	pcap_loop(descr,-1,my_callback,NULL);
}

void main(int argc, char **argv) {
	setbuf(stdout, NULL);
	setbuf(stderr, NULL);
	snifferLoop(argc, argv);
}
