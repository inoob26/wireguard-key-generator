import click
from datetime import datetime
from json import load as json_load, dump as json_dump
import requests
import os
from shutil import move
from pydantic import BaseModel

BASE_DIR = "/etc/wireguard"
INIT_FOLDERS = ("keys", "confs")

server_template = """
# {client_name}
[Peer]
PublicKey = {public_key}
AllowedIPs = {ip_addr}/32
"""


client_template = """
[Interface]
PrivateKey = {private_key}
Address = {ip_addr}/32
DNS = 8.8.8.8

[Peer]
PublicKey = {server_pub_key}
Endpoint = {server_ip_addr}:51830
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 20
"""


class WgClient(BaseModel):
    client: str
    ip: str
    created_at: datetime


def init_folders():
    # check if folder exists
    for folder in INIT_FOLDERS:
        if os.path.isdir(f"{BASE_DIR}/{folder}"):
            continue
        
        os.mkdir(f"{BASE_DIR}/{folder}")

def generate_keys(name: str):
    os.system(f'wg genkey | tee {BASE_DIR}/keys/{name}_private | wg pubkey | tee {BASE_DIR}/keys/{name}_public')
    # FOR test
    # with open(f"{BASE_DIR}/keys/{name}_private", "w") as f:
    #     f.write(f"{name}_private")

    # with open(f"{BASE_DIR}/keys/{name}_public", "w") as f:
    #     f.write(f"{name}_public")

def _client_config(
    config_name: str, server_pub_key: str, server_ip: str, private_key: str, ip_addr: str
):
    with open(f"{BASE_DIR}/confs/{config_name}", "w") as fl:
        data = f"{client_template}".format(
            private_key=private_key, 
            ip_addr=ip_addr, 
            server_pub_key=server_pub_key, 
            server_ip_addr=server_ip
        )
        fl.write(data)
    
    return f"{BASE_DIR}/confs/{config_name}"


def _server_config(client_name: str, public_key: str, ip: str):
    return server_template.format(
        client_name=client_name, public_key=public_key, ip_addr=ip
    )


# IP
def client_ip_addr(client_name: str):
    with open(f"{BASE_DIR}/db.json", "r") as f:
        data = json_load(f)

    ip_addr = ""
    for item in data["clients"]:
        if item["client"] != client_name:
            continue

        ip_addr = item["ip"]
    
    return ip_addr

def _get_server_ip():
    ip = requests.get("http://ifconfig.me")
    return ip.text


def _read_data_from_file(file_path: str) -> str:
    with open(f"{file_path}", "r") as f:
        data = f.read()
    
    return data


def _read_key(
    client_name: str = "",
    client_private_key: bool = False,
    client_pub_key: bool = False, 
    server_pub_key: bool = False,
):
    if client_name and client_private_key:
        key = _read_data_from_file(file_path=f"{BASE_DIR}/keys/{client_name}_private")
    
    if client_name and client_pub_key:
        key = _read_data_from_file(file_path=f"{BASE_DIR}/keys/{client_name}_public")

    if server_pub_key:
        key = _read_data_from_file(file_path=f"{BASE_DIR}/publickey")
    
    return key


def generate_config(client_name: str, server: bool = False, client: bool = False):
    # generate server config
    if client_name and server:
        # generate key
        generate_keys(name=client_name)

        # add client to db.json
        with open(f"{BASE_DIR}/db.json", "r") as f:
            data = json_load(f)

        last_ip = data["last_ip"]
        if client_name not in data["clients_names"]:
            # add name
            data["clients_names"].append(client_name)
                
            # gen new ip
            new_ip = int(last_ip.split(".")[-1]) + 1
            temp = last_ip.split(".")
            temp[-1] = str(new_ip)

            #update last_ip
            last_ip = ".".join(temp)
            data["last_ip"] = last_ip

            # gen new client
            client = WgClient(
                client=client_name,
                ip=last_ip,
                created_at=datetime.utcnow().isoformat()
            ).dict()
            client["created_at"] = client["created_at"].isoformat()
            data["clients"].append(client)

        # generate/write config to wg0.conf
        pub_key = _read_key(client_name=client_name, client_pub_key=True)
        config = _server_config(
            client_name=client_name,ip=data["last_ip"], public_key=pub_key
        )

        # Update db.json
        with open(f"{BASE_DIR}/db.json_new", "w") as f:
            json_dump(data, f, indent=4)

        # mv file
        move(src=f"{BASE_DIR}/db.json_new", dst=f"{BASE_DIR}/db.json")

        print(config)
    else:
        # generate client config
        client_private_key = _read_key(client_name=client_name, client_private_key=True)
        server_ip = _get_server_ip()
        server_pub_key = _read_key(server_pub_key=True)
        c_ip_addr = client_ip_addr(client_name=client_name)
        config_path = _client_config(
            config_name=f"{client_name}_wg.conf",
            server_ip=server_ip,
            server_pub_key=server_pub_key,
            private_key=client_private_key,
            ip_addr=c_ip_addr
        )

        print(config_path)

@click.command()
@click.option("--name", prompt="Your name")
def main(name):
    generate_config(client_name=name, server=True)
    generate_config(client_name=name, client=True)

if __name__ == '__main__':
    init_folders()
    main()
