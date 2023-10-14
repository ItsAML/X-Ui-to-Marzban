# main.py
import requests
from config import *
import logging
from datetime import datetime
import time
import json
import re

# Define the protocol (HTTP or HTTPS)
protocol = "https" if X_HTTPS else "http"

# Detecting Persian/Arabic Words
def contains_persian_arabic(text):
    persian_arabic_chars = "ابپتثجچحخدذرزژسشصضطظعغفقکگلمنهویئ"
    
    for char in text:
        if char in persian_arabic_chars:
            return True
    
    return False


# UserName Translater
def transliterate_basic(text):
    # Create a basic mapping of characters from Persian/Arabic to English
    transliteration_map = {
        'ا': 'a',
        'ب': 'b',
        'پ': 'p',
        'ت': 't',
        'ث': 'th',
        'ج': 'j',
        'چ': 'ch',
        'ح': 'h',
        'خ': 'kh',
        'د': 'd',
        'ذ': 'z',
        'ر': 'r',
        'ز': 'z',
        'ژ': 'zh',
        'س': 's',
        'ش': 'sh',
        'ص': 's',
        'ض': 'z',
        'ط': 't',
        'ظ': 'z',
        'ع': 'a',
        'غ': 'gh',
        'ف': 'f',
        'ق': 'q',
        'ک': 'k',
        'گ': 'g',
        'ل': 'l',
        'م': 'm',
        'ن': 'n',
        'ه': 'h',
        'و': 'w',
        'ی': 'y',
        'ئ': 'y',
        # Add more characters as needed
    }

    # Transliterate the text
    result = ''
    for char in text:
        if char in transliteration_map:
            result += transliteration_map[char]
        elif re.match(r'[a-zA-Z0-9]', char):
            # Keep English letters and digits as is
            result += char
        else:
            # Replace special characters and emojis with underscores
            result += '_'

    return result

# TimeStamp Converter X-UI
def milliseconds_to_seconds(seconds):
    if seconds < 0:
        current_timestamp = int(datetime.utcnow().timestamp())  # Get the current Unix timestamp
        future_timestamp = current_timestamp + abs(seconds / 1000.0)  # Subtract the absolute value of seconds
        return int(future_timestamp)
    else:
        return int(seconds / 1000.0)  # Convert to seconds

# Define the API endpoints
login_url = f"{protocol}://{X_DOMAIN}:{X_PORT}/login"
get_inbounds_url = f"{protocol}://{X_DOMAIN}:{X_PORT}/panel/api/inbounds/list"

def x_login(session, username, password):
    login_data = {
        "username": X_USERNAME,
        "password": X_PASSWORD
    }
    
    response = session.post(login_url, data=login_data)
    
    if response.status_code == 200:
        login_response = response.json()
        if login_response.get("success"):
            print("X-UI Login successful.")
            print("-" * 10)
            return True
        else:
            print("Login failed. Error message:", login_response.get("msg"))
    else:
        print("Failed to connect to the login endpoint.")
    return False

def get_x_inbounds(session):
    response = session.get(get_inbounds_url)
    
    if response.status_code == 200:
        inbounds_response = response.json()
        if inbounds_response.get("success"):
            inbounds_list = inbounds_response.get("obj")
            if inbounds_list:
                print("Inbounds:")
                
                # Create a list to store user data
                users = []
                
                for inbound in inbounds_list:
                    print("Inbound ID:", inbound.get("id"))
                    print("Remark:", inbound.get("remark"))
                    if "clientStats" in inbound:
                        client_stats = inbound["clientStats"]
                        
                        # Count the number of users for this inbound
                        num_users = len(client_stats)
                        print("Number of Users:", num_users)
                        print("*" * 9)
                        # Extract and store user data
                        for client in client_stats:
                            raw_email = client["email"]
                            email = contains_persian_arabic(client["email"])
                            if email:
                                raw_email = transliterate_basic(client["email"])

                            up = client["up"]
                            down = client["down"]
                            total = client["total"]
                            # Check if (up + down) is greater than total
                            if up + down <= total:
                                last_value = total - (up + down)
                                expiry_time = milliseconds_to_seconds(client["expiryTime"])
                                user_data = [raw_email, expiry_time, last_value]
                                users.append(user_data)
                            else:
                                # Skip storing the data
                                print("User skipped due to (up + down) greater than total")
                    else:
                        print("No Clients Found.")
                
                # Return the list of user data for later use
                return users
                
            else:
                print("No inbounds available.")
        else:
            print("Failed to get inbounds. Error message:", inbounds_response.get("msg"))
    else:
        print("Failed to connect to the get inbounds endpoint.")

def m_login(session,username, password):
    use_protocol = 'https' if M_HTTPS else 'http'
    url = f'{use_protocol}://{M_DOMAIN}:{M_PORT}/api/admin/token'
    data = {
        'username': M_USERNAME,
        'password': M_PASSWORD
    }

    try:
        response = session.post(url, data=data)
        response.raise_for_status()
        access_token = response.json()['access_token']
        print("Marzban Login Successful.")
        print("-" * 10)
        return access_token
    except requests.exceptions.RequestException as e:
        logging.error(f'Error occurred while obtaining access token: {e}')
        return None

def get_m_inbounds(session,access_token):
    use_protocol = 'https' if M_HTTPS else 'http'
    url = f'{use_protocol}://{M_DOMAIN}:{M_PORT}/api/inbounds'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        inboundsList = response.json()
        return inboundsList
    except requests.exceptions.RequestException as e:
        logging.error(f'Error occurred while retrieving inbounds: {e}')
        return None

def add_m_user(session, access_token, email, traffic, expiretime, inbounds):
    use_protocol = 'https' if M_HTTPS else 'http'
    url = f'{use_protocol}://{M_DOMAIN}:{M_PORT}/api/user'
    data = {
        "username": email,
        "proxies": {
            "vmess": {
            },
            "vless": {
            },
            "trojan": {
            },
            "shadowsocks": {
            }
        },
        "inbounds": {
        },
        "expire": expiretime,
        "data_limit": traffic,
        "data_limit_reset_strategy": "no_reset"
    }


    # Iterate through the protocols and check if inbounds exist
    for protocol, inbound_names in inbounds.items():
        if inbound_names:
            data["inbounds"][protocol] = inbound_names

    # Remove protocols with no inbounds
    data["proxies"] = {protocol: {} for protocol, inbs in data["inbounds"].items() if inbs}

    try:
        data["proxies"]["vless"]["flow"] = "xtls-rprx-vision"
    except Exception as e:
        pass

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    
    try:
        # Printing Json Data
        # print(json.dumps(data, indent=4))
        response = session.post(url,json=data, headers=headers)
        response.raise_for_status()
        user_status = response.json()
        return user_status
    except requests.exceptions.RequestException as e:
        logging.error(f'Error occurred while adding user: {e}')
        return None

def add_m_custom_user(session, access_token, email, traffic, expiretime, inbounds, flow):
    use_protocol = 'https' if M_HTTPS else 'http'
    url = f'{use_protocol}://{M_DOMAIN}:{M_PORT}/api/user'
    data = {
        "username": email,
        "proxies": {
            "vmess": {},
            "vless": {},
            "trojan": {},
            "shadowsocks": {}
        },
        "inbounds": {},
        "expire": expiretime,
        "data_limit": traffic,
        "data_limit_reset_strategy": "no_reset"
    }
    
    # Iterate through the protocols and check if inbounds exist
    for protocol, inbound_names in inbounds.items():
        if inbound_names:
            data["inbounds"][protocol] = inbound_names

    # Remove protocols with no inbounds
    data["proxies"] = {protocol: {} for protocol, inbs in data["inbounds"].items() if inbs}
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    # Conditionally add the "flow" line to the "vless" section
    if flow:
        try:
            data["proxies"]["vless"]["flow"] = "xtls-rprx-vision"
        except Exception as e:
            pass

    try:
        #print(json.dumps(data, indent=4))
        response = session.post(url, json=data, headers=headers)
        response.raise_for_status()
        user_status = response.json()
        return user_status
    except requests.exceptions.RequestException as e:
        logging.error(f'Error occurred while adding user: {e}')
        return None

def add_m_users(session, access_token, users, inbound_names):
    for user in users:
        email, expiretime, traffic = user
        user_status = add_m_user(session, access_token, email, traffic, expiretime, inbound_names)
        if user_status:
            print(f"User {email} added successfully.")
        else:
            print(f"Failed to add user {email}.")

def add_m_custom_users(session, access_token, users, inbound_names, flow):
    for user in users:
        email, expiretime, traffic = user
        user_status = add_m_custom_user(session, access_token, email, traffic, expiretime, inbound_names, flow)
        if user_status:
            print(f"User {email} added successfully.")
        else:
            print(f"Failed to add user {email}.")

if __name__ == "__main__":
    # Making Session For Each API
    X_SESSION = requests.Session()
    M_SESSION = requests.Session()
    if x_login(X_SESSION, X_USERNAME, X_PASSWORD):
        user_data = get_x_inbounds(X_SESSION)
        while True:
            choice = input("Do you wanna proceed to transfer users To Marzban? (y/n): ").strip().lower()
            
            if choice == 'y':
                auto_manual = input("Do you want to Transfer Users by Automatic Method or Manual Method? (a/m)").strip().lower()
                if auto_manual == "a":
                    # Getting Marzban Inbounds for Later Use
                    token = m_login(M_SESSION, M_USERNAME, M_PASSWORD)
                    if token:
                        all_inbounds = get_m_inbounds(M_SESSION, token)
                        protocols = {
                                    "vmess": [],
                                    "vless": [],
                                    "trojan": [],
                                    "shadowsocks": []
                                    }
                        # Loop through the keys in the JSON data
                        for key, value in all_inbounds.items():
                            # Check if the key is one of the supported protocols
                            if key in protocols:
                                protocols[key].extend([subprotocol["tag"] for subprotocol in value])

                        # Handle the possibility of missing protocols
                        for protocol in ["vmess", "vless", "trojan", "shadowsocks"]:
                            try:
                                protocols[protocol].extend([subprotocol["tag"] for subprotocol in all_inbounds[protocol]])
                            except KeyError:
                                pass
                        vmess_inbounds = ", ".join(protocols.get("vmess", []))
                        vless_inbounds = ", ".join(protocols.get("vless", []))
                        trojan_inbounds = ", ".join(protocols.get("trojan", []))
                        shadowsocks_inbounds = ", ".join(protocols.get("shadowsocks", []))
                        add_m_users(M_SESSION, token, user_data,protocols)
                        print("Users transferred to Marzban Succesfuly.")
                # Manual Adding Inbounds
                elif auto_manual == "m":
                        token = m_login(M_SESSION, M_USERNAME, M_PASSWORD)
                        if token:
                            all_inbounds = get_m_inbounds(M_SESSION, token)
                            custom_protocols = {
                            "vmess": [],
                            "vless": [],
                            "trojan": [],
                            "shadowsocks": []
                            }
                            # Loop through the keys in the JSON data
                            for key, value in all_inbounds.items():
                                # Check if the key is one of the supported protocols
                                if key in custom_protocols:
                                    custom_protocols[key].extend([subprotocol["tag"] for subprotocol in value])

                            # Handle the possibility of missing protocols
                            vmess_inbounds = []
                            while True:
                                print("VMESS inbound names. (You Can Type '/' To Select All)")
                                available_inbounds = ", ".join(custom_protocols.get("vmess", []))
                                print("Available Inbounds:", available_inbounds or "No Inbounds Found")
                                vmess_input = input("Enter Inbound Name: (Press Enter While Empty To Skip)")
                                if vmess_input:
                                    if vmess_input == "/":
                                        vmess_inbounds.extend(custom_protocols.get("vmess", []))
                                        break
                                    else:
                                        vmess_inbounds.append(vmess_input)
                                else:
                                    break

                            vless_inbounds = []
                            while True:
                                print("VLESS inbound names. (You Can Type '/' To Select All)")
                                available_inbounds = ", ".join(custom_protocols.get("vless", []))
                                print("Available Inbounds:", available_inbounds or "No Inbounds Found")
                                vless_input = input("Enter Inbound Name: (Press Enter While Empty To Skip)")
                                if vless_input:
                                    if vless_input == "/":
                                        vless_inbounds.extend(custom_protocols.get("vless", []))
                                        break
                                    else:
                                        vless_inbounds.append(vless_input)
                                else:
                                    break

                            trojan_inbounds = []
                            while True:
                                print("TROJAN inbound names. (You Can Type '/' To Select All)")
                                available_inbounds = ", ".join(custom_protocols.get("trojan", []))
                                print("Available Inbounds:", available_inbounds or "No Inbounds Found")
                                trojan_input = input("Enter Inbound Name: (Press Enter While Empty To Skip)")
                                if trojan_input:
                                    if trojan_input == "/":
                                        trojan_inbounds.extend(custom_protocols.get("trojan", []))
                                        break
                                    else:
                                        trojan_inbounds.append(trojan_input)
                                else:
                                    break

                            shadowsocks_inbounds = []
                            while True:
                                print("SHADOWSOCKS inbound names. (You Can Type '/' To Select All)")
                                available_inbounds = ", ".join(custom_protocols.get("shadowsocks", []))
                                print("Available Inbounds:", available_inbounds or "No Inbounds Found")
                                shadowsocks_input = input("Enter Inbound Name: (Press Enter While Empty To Skip)")
                                if shadowsocks_input:
                                    if shadowsocks_input == "/":
                                        shadowsocks_inbounds.extend(custom_protocols.get("shadowsocks", []))
                                        break
                                    else:
                                        shadowsocks_inbounds.append(shadowsocks_input)
                                else:
                                    break
                            while True:
                                print("Do you Want To Use Flow For Vless Inbounds? (xtls-rprx-vision)")
                                fl_ow = input("Enter (y/n) : ").strip().lower()
                                if fl_ow == "y":
                                    flow_status = True
                                    break
                                if fl_ow == "n":
                                    flow_status = False
                                    break
                                else:
                                    print("please enter valid answer")
                            
                            customprotocols = {
                                "vmess": ",".join(vmess_inbounds).split(",") if vmess_inbounds else [],
                                "vless": ",".join(vless_inbounds).split(",") if vless_inbounds else [],
                                "trojan": ",".join(trojan_inbounds).split(",") if trojan_inbounds else [],
                                "shadowsocks": ",".join(shadowsocks_inbounds).split(",") if shadowsocks_inbounds else []
                            }

                            # Filter out empty values
                            customprotocols = {k: v for k, v in customprotocols.items() if v}
                            add_m_custom_users(M_SESSION, token, user_data,customprotocols,flow_status)
                else:
                    print("Invalid choice. Please enter 'a' or 'm'.")

                break
            elif choice == 'n':
                print("Exiting the Script.")
                break
            else:
                print("Invalid choice. Please enter 'y' or 'n'.")

# https://github.com/ItsAML
