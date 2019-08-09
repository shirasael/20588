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

struct ether_header {
	u_int8_t ether_dhost[ETH_ALEN]; /* 6 bytes destination */
	u_int8_t ether_shost[ETH_ALEN]; /* 6 bytes source addr */
	u_int16_t ether_type; /* 2 bytes ID type */
} __attribute__ ((__packed__));

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
		printf("%sn",errbuf);
		exit(1);
	}
	printf("DEV: %sn",dev);
	
	/* ask pcap for the network address and mask of the device */
	pcap_lookupnet(dev,&netp,&maskp,errbuf);
	descr = pcap_open_live(dev,BUFSIZ, 0, -1,errbuf);

	/* BUFSIZ is max packet size to capture, 0 is promiscous, -1 means don’t wait for read to time out. */
	if(descr == NULL) {
		printf("pcap_open_live(): %sn",errbuf);
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

	descr = openGoLiveAndSetFilter();

	packet = pcap_next(descr, &hdr);

	if (packet == NULL) {
		printf("It got away!n");
	} else {
		printf(“one lonely packet.n”);
	}
}

void my_callback(u_char *useless,const struct pcap_pkthdr* pkthdr,const u_char* packet) { 
//do stuff here with packet 
}

void snifferLoop(int argc, char **argv) {
	pcap_t* descr; /* pointer to device descriptor */

	descr = openGoLiveAndSetFilter();

	pcap_loop(descr,-1,my_callback,NULL);
}

