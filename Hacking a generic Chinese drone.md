This repository documents the process of how I hacked a generic Chinese drone to automate it with OpenCV and YOLOv8 (python).

First step was to fire up the drone in it's default environment, which means it's base setup : 
![[Pasted image 20250427212217.png]]

In a second time we want to get the image data ; My first thought was to sniff the packets sent between the iPad and the drone, so I wanted to connect to the drone wifi :
![[Pasted image 20250427212800.png]]

But here's the first challenge, the only one device can connect to the drone, the rest will get an error while trying to connect. So we can establish this "map" (lol) of the network, those ips are static and can't change.

![[Pasted image 20250427212939.png]]

After trying many things to enter the network to sniff the packets I came across this [Apple Developer documentation page](https://developer.apple.com/documentation/network/recording-a-packet-trace)  which basically teaches us that binary `rvictl` on MacOS permits us to "mirror" an apple mobile device's network communications on an rvi0 interface. 
![[Pasted image 20250427232635.png]]


Unlike many people, I do not own an Apple laptop, so I found [this GitHub repo](https://github.com/gh2o/rvi_capture) that basically does the same but for Linux and Windows.
![[Pasted image 20250427232828.png]]

After making sure we have the proper setup (*iTunes installed and Apple mobile device support running*) to run the tool, we can create a `pcapng` file to later read with [Wireshark](https://www.wireshark.org/).

```powershell
& "C:/Python/Python310/python.exe" rvi_capture --udid "[apple device udid]" <output>
```

This command gives us a network capture file that has the info we need to understand the drones anatomy.

![[Pasted image 20250427235722.png]]

Once opened in Wireshark we can see a bunch of irrelevant ICMP / UDP traffic between the drone and the iPhone. After a little bit of quite random and general exploration of the packets I found a very interesting conversation between the drone and the iPhone : ![[Pasted image 20250428000046.png]]

We'll follow this TCP stream to see the full conversation between the two hosts ![[Pasted image 20250428000132.png]]
![[Pasted image 20250428000151.png]]

In this very first TCP stream we can observe a lot of notable things, 
1) The video from the drone is sent via RTSP protocol
   ![[Pasted image 20250428000317.png]]
   In the request the Apple device uses method OPTIONS on `rtsp://192.168.1.1:7070/webcam` using RTSP 1.0 
   
   Server / Drone answers with possible methods, at the time I didn't know much about RTSP so here's a rough explanation of each method : 
   
   ``DESCRIBE`` → Requests details about the media stream.
   ``SETUP`` → Establishes a session and prepares the media stream.
   ``PLAY`` → Starts or resumes delivery of the media stream.
   ``PAUSE`` → Temporarily halts the media stream without ending the session.
   ``TEARDOWN`` → Terminates the session and releases resources.

2) We also get to know some information about the video details of the stream
   ![[Pasted image 20250428000914.png]]
   We know that this is request #2 and the payload is an SDP file (session description protocol.)
   For some reason the session name is "Test", which is curious given the fact that those drone were for sale for years.
   We are also given the information that this is a broadcast stream, not a private one and some connection info. `m=video 0 RTP/AVP 26` is the media type.
   
3) Here the server gives out what looks like a session ID / token 
   ![[Pasted image 20250428004458.png]]
   It will be very useful for the next steps.
   .
4) This basically starts the drone camera stream, using the previously given session id / token.
   ![[Pasted image 20250428004534.png]]
   ==Note : This ID NEVER changes on the model shipped (tested with 2 drones April 28 2025)==
   This could be a major security flaw.


After understanding the back and forth communication between those two devices 