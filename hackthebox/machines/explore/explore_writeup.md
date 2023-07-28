# Explore

Explore is an _easy_ **Android** machine that was released on 26/06/2021

**Note**: this write-up is quite short and concise as it's based on really brief notes that were taken just for convenience during the pwning of the machine. 

## Enumeration

As usual we start by performing a port scan with nmap

```
nmap -A 10.10.10.247 -p- | tee portscan.txt

Starting Nmap 7.91 ( https://nmap.org ) at 2021-08-10 19:32 EDT
Nmap scan report for explore.htb (10.10.10.247)
Host is up (0.060s latency).
Not shown: 65530 closed ports
PORT      STATE    SERVICE VERSION
2222/tcp  open     ssh     (protocol 2.0)
| fingerprint-strings: 
|   NULL: 
|_    SSH-2.0-SSH Server - Banana Studio
| ssh-hostkey: 
|_  2048 71:90:e3:a7:c9:5d:83:66:34:88:3d:eb:b4:c7:88:fb (RSA)
5555/tcp  filtered freeciv
32831/tcp open     unknown
| fingerprint-strings: 
|   GenericLines: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 10 Aug 2021 23:34:13 GMT
|     Content-Length: 22
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Invalid request line:
|   GetRequest: 
|     HTTP/1.1 412 Precondition Failed
|     Date: Tue, 10 Aug 2021 23:34:13 GMT
|     Content-Length: 0
|   HTTPOptions: 
|     HTTP/1.0 501 Not Implemented
|     Date: Tue, 10 Aug 2021 23:34:18 GMT
|     Content-Length: 29
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Method not supported: OPTIONS
|   Help: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 10 Aug 2021 23:34:33 GMT
|     Content-Length: 26
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Invalid request line: HELP
|   RTSPRequest: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 10 Aug 2021 23:34:18 GMT
|     Content-Length: 39
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     valid protocol version: RTSP/1.0
|   SSLSessionReq: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 10 Aug 2021 23:34:33 GMT
|     Content-Length: 73
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Invalid request line: 
|     ?G???,???`~?
|     ??{????w????<=?o?
|   TLSSessionReq: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 10 Aug 2021 23:34:33 GMT
|     Content-Length: 71
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Invalid request line: 
|     ??random1random2random3random4
|   TerminalServerCookie: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 10 Aug 2021 23:34:33 GMT
|     Content-Length: 54
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Invalid request line: 
|_    Cookie: mstshash=nmap
42135/tcp open     http    ES File Explorer Name Response httpd
|_http-title: Site doesn't have a title (text/html).
59777/tcp open     http    Bukkit JSONAPI httpd for Minecraft game server 3.6.0 or older
|_http-title: Site doesn't have a title (text/plain).
2 services unrecognized despite returning data. If you know the service

[...]

Network Distance: 2 hops
Service Info: Device: phone

TRACEROUTE (using port 3306/tcp)
HOP RTT      ADDRESS
1   56.70 ms 10.10.14.1
2   59.35 ms explore.htb (10.10.10.247)

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 159.51 seconds

```

- SSH on **port 2222** is not accessible with common credentials like admin:admin, root:root etc.
If nothing else work we can try bruteforcing it with some dictionary

- **Port 5555** is marked by nmap as freeciv, but with the machine being an Android phone it is way more likely to be an ADB (Android Debug Bridge) service. The port is filtered so we can't do much for now, but we should keep this in mind.


- The service on **port 42135** is the ES File Explorer, from which the machine probably takes its name.

## Foothold

A quick search on the internet shows that ES File Explorer is actually vulnerable to [CVE-2019-6447](https://www.cvedetails.com/cve/CVE-2019-6447/), which is an arbitrary file read.

`searchsploit ES file explorer`

provides us the exploit.

Once we download the files from the device, we find an interesting picture with some credentials on it:

`kristi:Kr1sT!5h@Rp3xPl0r3!`

With can use this creds to ssh into the machine as kristi and get the user.txt flag

## Privesc
Now that we're actually into the machine, we can make use of the 5555 ADB port that we found during our enumeration phase. It is filtered, therefore not accessible from outside the machine, but since we have SSH access we can tunnel the connection and successfully access adb.

`ssh -NL 5554:localhost:5554 -L 5555:localhost:5555 kristi@explore.htb -p 2222`

This command creates the tunnel

Now we can use [PhoneSploit](https://github.com/aerosol-can/PhoneSploit) to establish the connection via adb

We launch PhoneSploit, connect to localhost:5555 and get a shell on the device.

From here, we can become root by simply running

`su root`

and the root.txt flag is located at

`/data/root.txt`