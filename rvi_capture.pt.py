from scapy.all import *
import time

# Read PCAP
packets = rdpcap("capture")  # Replace with your file

SRC_IP = "192.168.1.100"  # Your source
previous_time = None

for pkt in packets:
    if IP in pkt and pkt[IP].src == SRC_IP:
        # If pcap has timestamps
        if previous_time:
            delay = pkt.time - previous_time
            if delay > 0:
                time.sleep(delay)
        previous_time = pkt.time

        send(pkt)