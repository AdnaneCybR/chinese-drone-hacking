This repository documents the process of how I hacked a generic Chinese drone to automate it with OpenCV and YOLOv8 (Python).

First step was to fire up the drone in its default environment, which means its base setup:  
![Drone Startup](images/Pasted%20image%2020250427212217.png)

In a second time, we want to get the image data; my first thought was to sniff the packets sent between the iPad and the drone, so I wanted to connect to the drone wifi:  
![Connecting to Drone](images/Pasted%20image%2020250427212800.png)

But here's the first challenge: only one device can connect to the drone, the rest will get an error while trying to connect. So we can establish this "map" (lol) of the network — these IPs are static and can't change:  
![Network Map](images/Pasted%20image%2020250427212939.png)

After trying many things to enter the network to sniff the packets, I came across this [Apple Developer documentation page](https://developer.apple.com/documentation/network/recording-a-packet-trace), which basically teaches us that the binary `rvictl` on MacOS lets you "mirror" an Apple mobile device's network communications on an rvi0 interface:  
![Apple Doc](images/Pasted%20image%202025042732635.png)

Unlike many people, I do not own an Apple laptop, so I found [this GitHub repo](https://github.com/gh2o/rvi_capture) that basically does the same but for Linux and Windows:  
![rvi_capture Repo](images/Pasted%20image%202025042732828.png)

After making sure we have the proper setup (*iTunes installed and Apple Mobile Device support running*) to run the tool, we can create a `pcapng` file to later read with [Wireshark](https://www.wireshark.org/):

```powershell
& "C:/Python/Python310/python.exe" rvi_capture --udid "[apple device udid]" <output>
```

This command gives us a network capture file that has the info we need to understand the drone's anatomy:  
![pcap File](images/Pasted%20image%202025042735722.png)

Once opened in Wireshark, we can see a bunch of irrelevant ICMP/UDP traffic between the drone and the iPhone. After a little bit of random and general exploration of the packets, I found a very interesting conversation between the drone and the iPhone:  
![Interesting Conversation](images/Pasted%20image%202025042800046.png)

We'll follow this TCP stream to see the full conversation between the two hosts:  
![TCP Stream](images/Pasted%20image%202025042800132.png)  
![More TCP Stream](images/Pasted%20image%202025042800151.png)

In this very first TCP stream we can observe a lot of notable things:

1. **The video from the drone is sent via RTSP protocol**  
   ![RTSP Info](images/Pasted%20image%202025042800317.png)

   In the request, the Apple device uses method OPTIONS on `rtsp://192.168.1.1:7070/webcam` using RTSP 1.0.  
   The server (drone) answers with possible methods.  
   Here's a rough explanation of each method:
   
   - `DESCRIBE` → Requests details about the media stream.
   - `SETUP` → Establishes a session and prepares the media stream.
   - `PLAY` → Starts or resumes delivery of the media stream.
   - `PAUSE` → Temporarily halts the media stream without ending the session.
   - `TEARDOWN` → Terminates the session and releases resources.

2. **We also get some info about the video details of the stream**  
   ![Video Details](images/Pasted%20image%202025042800914.png)

   - This is request #2 and the payload is an SDP file (Session Description Protocol).
   - Session name is "Test" (which is wild since these drones were commercially sold lol).
   - The stream is public (broadcast), not private.
   - `m=video 0 RTP/AVP 26` → media type info.

3. **The server spits out what looks like a session ID/token**  
   ![Session ID](images/Pasted%20image%2020250428004534.png) <!-- You forgot to finish the last image reference. Just plug the correct filename here. -->

