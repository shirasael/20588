#include <pcap.h>
#include <stdio.h> 
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/if_ether.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <string.h>
#include "packetPrinter.h"

#define ETHERTYPE_IP 0x0800 /* IP */
#define ETHERTYPE_ARP 0x0806 /* Address resolution */ 

void print_device_info(const bpf_u_int32* ip_raw, const bpf_u_int32* subnet_mask_raw) {
	char ip[18];
	char subnet_mask[18];
	struct in_addr address;

	address.s_addr = *ip_raw;
	strcpy(ip, inet_ntoa(address));
	if (ip == NULL) {
		perror("inet_ntoa"); /* print error */
		return;
	}

	/* Get subnet mask in human readable form */
	address.s_addr = *subnet_mask_raw;
	strcpy(subnet_mask, inet_ntoa(address));
	if (subnet_mask == NULL) {
		perror("inet_ntoa");
		return;
	}

	printf("IP address: %s\n", ip);
	printf("Subnet mask: %s\n\n", subnet_mask);
}

pcap_t* open_go_live_and_set_filter(char* filter) {
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
	print_device_info(&netp, &maskp);

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

void sniff_one_packet(char* filter) {
	struct pcap_pkthdr hdr; /* struct: packet header */
	pcap_t* descr; /* pointer to device descriptor */
	const u_char *packet; /* pointer to packet */

	descr = open_go_live_and_set_filter(filter);

	packet = pcap_next(descr, &hdr);

	if (packet == NULL) {
		printf("It got away!\n");
	} else {
		printf("One lonely packet.\n\n");
		got_packet(NULL, &hdr, packet);
	}
}

void sniffer_loop(char* filter) {
	pcap_t* descr; /* pointer to device descriptor */
	descr = open_go_live_and_set_filter(filter);
	pcap_loop(descr,-1,got_packet,NULL);
}

void main(int argc, char **argv) {
	setbuf(stdout, NULL);
	setbuf(stderr, NULL);
	char* filter = NULL;

	if (argc < 2) {
		printf("USAGE: libpcap_demo [sniff|fetch-one] [filter]\n");
		return;
	} else if (argc > 2) {
		filter = argv[2];
		printf("Using filter: %s\n", filter);
	}
	
	if (strcmp(argv[1], "sniff") == 0) {
		printf("Sniffing!\n");
		sniffer_loop(filter);
	} else if (strcmp(argv[1], "fetch-one") == 0) {
		printf("Fetching one packet...\n");
		sniff_one_packet(filter);
	}
}
