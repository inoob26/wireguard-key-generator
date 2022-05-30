## Prepare files

0. install python dependency
    ```
    python3 -m pip install -r req.txt
    ```

1. rename db.json.template to db.json
    ```bash
    cp ./db.json.template ./db.json
    ```
2. change last_ip in db.json to your own network ip address.

For example in wireguard default network is 10.0.0.0/8 and server address is 10.0.0.1. 

You should set "last_ip" as 10.0.0.1 and after that the script will increment ip addresses

3. in main.py you have to set BASE_DIR 
    ```python3
    ...
    BASE_DIR = "/etc/wireguard"
    ...
    ```
## Generate server and client keys
1. run key generator
    ```
    python3 main.py --name <client-name>
    ```
2. copy output to wg0.conf

    output look like
    ```
    udwfMasdsadsadsddsasdkjasoidhughfasd=

    # <client-name>
    [Peer]
    PublicKey = udwfMasdsadsadsddsasdkjasoidhughfasd=

    AllowedIPs = 10.0.0.29/32

    /<BASE_DIR>/confs/<client-name>_wg.conf
    ```

    You have to copy 
    ```
    # <client-name>
    [Peer]
    PublicKey = udwfMasdsadsadsddsasdkjasoidhughfasd=

    AllowedIPs = 10.0.0.29/32
    ```

    and paste it to wireguard config file (by default /etc/wireguard/wg0.conf)

3. send /<BASE_DIR>/confs/<client-name>_wg.conf to client

4. restart wireguard service 
    ```
    systemctl restart wg-quick@wg0
    ```