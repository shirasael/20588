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

void print_packet_info(const struct pcap_pkthdr* pkthdr, const u_char* packet);

void print_device_info(const bpf_u_int32& ip_raw, const bpf_u_int32& subnet_mask_raw) {
	struct in_addr address;
	address.s_addr = *ip_raw;
	strcpy(ip, inet_ntoa(address));
	if (ip == NULL) {
		perror("inet_ntoa"); /* print error */
		return 1;
	}
	printf("IP address: %s\n", ip);

	/* Get subnet mask in human readable form */
	address.s_addr = *subnet_mask_raw;
	strcpy(subnet_mask, inet_ntoa(address));
	if (subnet_mask == NULL) {
		perror("inet_ntoa");
		return 1;
	}

	printf("IP address: %s\n", ip);
	printf("Subnet mask: %s\n", subnet_mask);
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
	print_device_info(netp, masp);

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

void sniff_one_packet(int argc, char **argv) {
	struct pcap_pkthdr hdr; /* struct: packet header */
	pcap_t* descr; /* pointer to device descriptor */
	const u_char *packet; /* pointer to packet */

	descr = open_go_live_and_set_filter(NULL);

	packet = pcap_next(descr, &hdr);

	if (packet == NULL) {
		printf("It got away!\n");
	} else {
		printf("one lonely packet.\n");
	}
}

void my_callback(u_char* unused, const struct pcap_pkthdr* pkthdr,const u_char* packet) { 
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
		printf("IP. Let's look into it...\n");
		print_packet_info(pkthdr, packet);
	} else  if (ntohs(eth_header->ether_type) == ETHERTYPE_ARP) {
		printf("ARP\n");
	} else  if (ntohs(eth_header->ether_type) == ETHERTYPE_REVARP) {
		printf("Reverse ARP\n");
	}
}

void print_packet_info(const struct pcap_pkthdr* header, const u_char* packet) {
	/* First, lets make sure we have an IP packet */
	struct ether_header *eth_header;
	eth_header = (struct ether_header *) packet;
	if (ntohs(eth_header->ether_type) != ETHERTYPE_IP) {
		printf("Not an IP packet. Skipping...\n\n");
		return;
	}

	/* The total packet length, including all headers
	and the data payload is stored in
	header->len and header->caplen. Caplen is
	the amount actually available, and len is the
	total packet length even if it is larger
	than what we currently have captured. If the snapshot
	length set with pcap_open_live() is too small, you may
	not have the whole packet. */
	printf("Total packet available: %d bytes\n", header->caplen);
	printf("Expected packet size: %d bytes\n", header->len);

	/* Pointers to start point of various headers */
	const u_char *ip_header;
	const u_char *tcp_header;
	const u_char *payload;

	/* Header lengths in bytes */
	int ethernet_header_length = 14; /* Doesn't change */
	int ip_header_length;
	int tcp_header_length;
	int payload_length;

	/* Find start of IP header */
	ip_header = packet + ethernet_header_length;
	/* The second-half of the first byte in ip_header
	contains the IP header length (IHL). */
	ip_header_length = ((*ip_header) & 0x0F);
	/* The IHL is number of 32-bit segments. Multiply
	by four to get a byte count for pointer arithmetic */
	ip_header_length = ip_header_length * 4;
	printf("IP header length (IHL) in bytes: %d\n", ip_header_length);

	/* Now that we know where the IP header is, we can
	inspect the IP header for a protocol number to
	make sure it is TCP before going any further.
	Protocol is always the 10th byte of the IP header */
	u_char protocol = *(ip_header + 9);
	if (protocol != IPPROTO_TCP) {
		printf("Not a TCP packet. Skipping...\n\n");
		return;
	}

	/* Add the ethernet and ip header length to the start of the packet
	to find the beginning of the TCP header */
	tcp_header = packet + ethernet_header_length + ip_header_length;
	/* TCP header length is stored in the first half
	of the 12th byte in the TCP header. Because we only want
	the value of the top half of the byte, we have to shift it
	down to the bottom half otherwise it is using the most
	significant bits instead of the least significant bits */
	tcp_header_length = ((*(tcp_header + 12)) & 0xF0) >> 4;
	/* The TCP header length stored in those 4 bits represents
	how many 32-bit words there are in the header, just like
	the IP header length. We multiply by four again to get a
	byte count. */
	tcp_header_length = tcp_header_length * 4;
	printf("TCP header length in bytes: %d\n", tcp_header_length);

	/* Add up all the header sizes to find the payload offset */
	int total_headers_size = ethernet_header_length + ip_header_length + tcp_header_length;
	printf("Size of all headers combined: %d bytes\n", total_headers_size);
	payload_length = header->caplen -
		(ethernet_header_length + ip_header_length + tcp_header_length);
	printf("Payload size: %d bytes\n", payload_length);
	payload = packet + total_headers_size;
	printf("Memory address where payload begins: %p\n\n", payload);
}

void sniffer_loop(int argc, char **argv) {
	pcap_t* descr; /* pointer to device descriptor */
	char* filter = NULL;
	if (argc > 1) {
		filter = argv[1];
		printf("Using filter: %s\n", filter);
	}
	descr = open_go_live_and_set_filter(filter);
	pcap_loop(descr,-1,my_callback,NULL);
}

void main(int argc, char **argv) {
	setbuf(stdout, NULL);
	setbuf(stderr, NULL);
	sniffer_loop(argc, argv);
}
