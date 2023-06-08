import subprocess
import os
import pyuac
import ctypes
import time
import json
import tempfile
import sys
import threading
from input_sanitizer import convert_keystrokes_fa_to_en
from updater import updater, check_latest_release
from dns_providers import DNS_PROVIDERS
from version import VERSION


# Run as admin
if not ctypes.windll.shell32.IsUserAnAdmin():
    # Re-launch the script with elevated privileges
    pyuac.runAsAdmin()


CONFIG_FILE = "config.json"
target_nic_name = None
detected_nic_name = None

# Update status
is_update_available = False


def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            global target_nic_name
            target_nic_name = json.load(file)
    except Exception:
        pass


def save_config():
    try:
        with open(CONFIG_FILE, "w") as file:
            file.write(json.dumps(target_nic_name))
    except Exception:
        pass


header = f"""\x1b[92;1m     __        __           ___ ___ 
\ / /  \ |  | |__)    |\ | |__   |  
 |  \__/ \__/ |  \    | \| |___  |  
                                    
                     __   ___  __  
|\/|  /\  |\ |  /\  / _` |__  |__) 
|  | /~~\ | \| /~~\ \__> |___ |  \   v{VERSION}\x1b[0m"""

bye_message = """\x1b[36;49;1m
     _             _         
    / `_  _   _/  /_)   _   /
   /_;/_//_//_/  /_)/_//_' . 
                    _/       
\x1b[0m"""


def get_all_nic_details():
    output = subprocess.check_output(
        ["netsh", "interface", "ipv4", "show", "interface"]
    )

    output_str = ""
    try:
        output_str = output.decode(errors="ignore")
    except Exception:
        try:
            # Store the output that caused an exception when decoding
            with open(
                tempfile.gettempdir() + "\dns-changer_decode-exception.bin", "wb"
            ) as file:
                file.write(output)
        except Exception:
            pass
        print(
            "\nAn exception has occurred! Please send this file to the developers:\n"
            + tempfile.gettempdir()
            + "\dns-changer_decode-exception.bin"
        )
        input()
        raise

    nic_list = []
    for line in output_str.split("\n"):
        line = line.strip()
        if (
            ("connected" in line)
            and ("Loopback" not in line)
            and ("disconnected" not in line)
        ):
            parts = line.split()
            try:
                nic_list.append(
                    {
                        "index": int(parts[0]),
                        "metric": int(parts[1]),
                        "status": parts[3],
                        "name": " ".join([n for n in parts[4:]]),
                    }
                )
            except Exception:
                pass

    return nic_list


def detect_default_network_interface():
    nics = get_all_nic_details()
    result = None
    try:
        result = nics[0]
    except Exception:
        pass

    for nic in nics:
        if nic["status"] == "connected" and result["status"] == "disconnected":
            result = nic
        elif nic["status"] == "connected" and nic["metric"] < result["metric"]:
            result = nic

    return result["name"]


# Checks what DNS is set on a network interface.
def DNS_check(nic_name):
    # Run the 'ipconfig' command and capture its output
    output = subprocess.check_output(["ipconfig", "/all"])

    # Convert the output to a string
    output_str = ""
    try:
        output_str = output.decode(errors="ignore")
    except Exception:
        try:
            # Store the output that caused an exception when decoding
            with open(
                tempfile.gettempdir() + "\dns-changer_decode-exception.bin", "wb"
            ) as file:
                file.write(output)
        except Exception:
            pass
        print(
            "\nAn exception has occurred! Please send this file to the developers:\n"
            + tempfile.gettempdir()
            + "\dns-changer_decode-exception.bin"
        )
        input()
        raise

    # Separate result for each network adapter
    output_parts = output_str.split("\r\n\r\n")

    report = None
    try:
        i = 0
        while i < len(output_parts):
            if f"adapter {nic_name}:" in output_parts[i]:
                report = output_parts[i] + "\r\n" + output_parts[i + 1]
            i = i + 1
    except Exception:
        pass

    # Check if DHCP Server is equal to DNS Server for the specified adapter.
    if report and "DNS Servers . . . . . . . . . . . :" in report:
        dns_servers = []
        dhcp_server = None

        try:
            i = 0
            report_lines = report.split("\n")
            while i < len(report_lines):
                line = report_lines[i]
                if "DNS Servers" in line:
                    dns_servers.append(line.strip().split(":")[1].strip())
                    if i < len(report_lines) - 1:
                        next_line = report_lines[i + 1]
                        next_line_parts = next_line.split(":")
                        if len(next_line_parts) == 1 and len(next_line.strip()) > 0:
                            dns_servers.append(next_line.strip())
                i = i + 1
        except Exception:
            pass

        try:
            dhcp_server = [
                line.strip().split(":")[1].strip()
                for line in report.split("\n")
                if "DHCP Server" in line
            ][0]
        except Exception:
            pass

        if dhcp_server and len(dns_servers) == 1 and dns_servers[0] == dhcp_server:
            return f"\x1b[34;1mOh! DNS Server Not set for\x1b[0m {nic_name}"

        if len(dns_servers) > 1:
            for provider in DNS_PROVIDERS.keys():
                if (
                    DNS_PROVIDERS[provider][0] == dns_servers[0]
                    and DNS_PROVIDERS[provider][1] == dns_servers[1]
                ):
                    return f"\x1b[32;1mYes! {provider} DNS Server is set for\x1b[0m {nic_name}"

        return f"\x1b[33;1mUnknown DNS is set for\x1b[0m {nic_name}"

    else:
        return f"Oops!!! No DNS found for {nic_name}"


# Sets DNS.
def set_DNS(nic_name, provider):
    primary_dns = DNS_PROVIDERS[provider][0]
    secondary_dns = DNS_PROVIDERS[provider][1]

    # Set the preferred DNS server
    if (
        os.system(f'netsh interface ip set dns name="{nic_name}" static {primary_dns}')
        == 0
    ):
        print("\x1b[92;1mPreferred DNS server set successfully\x1b[0m")
        time.sleep(0.1)
    else:
        print(" \x1b[31;1mError setting preferred DNS server\x1b[0m")
        time.sleep(1)
    # Set the alternate DNS server
    if (
        os.system(
            f'netsh interface ip add dns name="{nic_name}" {secondary_dns} index=2'
        )
        == 0
    ):
        print("\x1b[92;1mAlternate DNS server added successfully\x1b[0m")
        time.sleep(1)
    else:
        print(" \x1b[31;1mError adding alternate DNS server\x1b[0m")
        time.sleep(1)


load_config()


# Cheack for new updates
def check_Update():
    result = check_latest_release()
    if not result:
        return None
    if result and result["version"] != VERSION:
        global is_update_available
        is_update_available = True
        return True
    else:
        return False


updater_thread = threading.Thread(target=check_Update)
updater_thread.start()

selected_option = None
# Main process runs here.
while selected_option != "q":
    # Clear the console screen
    os.system("cls" if os.name == "nt" else "clear")

    file_path = sys.argv[0]
    file_name = file_path.split("\\")[-1]

    # Print the header text with the current options
    print(header + "\n")

    # Print DNS status of the network interface
    if target_nic_name:
        nics = get_all_nic_details()
        exists = False
        for nic in nics:
            if nic["name"] == target_nic_name:
                exists = True

        DNS_status = DNS_check(target_nic_name)

        if exists:
            print(f" Selected network adapter ==> \x1b[33;1m{target_nic_name}\x1b[0m")
            print(" " + DNS_status)
            print("-----------------------------------------------" + "\n")
        else:
            print(
                f" Selected network adapter ==> \x1b[33;1m{target_nic_name}\x1b[0m  \x1b[37;41;1mNot Available!\x1b[0m"
            )
            print(" " + DNS_status)
            print("-----------------------------------------------" + "\n")

    else:
        detected_nic_name = detect_default_network_interface()
        DNS_status = DNS_check(detected_nic_name)
        print(f" Detected network adapter ==> \x1b[33;1m{detected_nic_name}\x1b[0m")
        print(" " + DNS_status)
        print("-----------------------------------------------" + "\n")

    nic_name = target_nic_name if target_nic_name is not None else detected_nic_name

    # Print menu options
    for i, DNS in enumerate(DNS_PROVIDERS):
        print("  {}. {}".format(i + 1, DNS))
    print()
    print("  C. Clear DNS (auto)")
    print("  F. Flush DNS cache")
    print("  N. Choose network adapter")
    if is_update_available:
        print("  U. Update \x1b[38;5;119m(New version available)\x1b[0m")
    else:
        print("  U. Update")
    print("  Q. Exit")
    print("\n" + "-----------------------------------------------" + "\n")

    selected_option = input("\x1b[36;49;1m  Your choice:\x1b[0m ")
    selected_option = convert_keystrokes_fa_to_en(selected_option).lower()

    if selected_option.isdigit() and int(selected_option) <= len(DNS_PROVIDERS):
        # Do something for the selected option
        chosen_dns_index = int(selected_option) - 1
        selected_DNS = list(DNS_PROVIDERS.keys())[chosen_dns_index]
        print("You selected: {}".format(selected_DNS))
        set_DNS(nic_name, selected_DNS)

    elif selected_option == "q":
        # Exit the loop
        os.system("cls" if os.name == "nt" else "clear")
        print(bye_message)
        time.sleep(2)

    elif selected_option == "c":
        # Define the command to remove DNS from the network adapter
        command = f'netsh interface ipv4 delete dns "{nic_name}" all'
        if os.system(command) == 0:
            print("\x1b[35;47;1mDNS successfuly disabled.\x1b[0m")
        time.sleep(1.5)

    elif selected_option == "f":
        # Define the command to flush DNS cache
        command = f"ipconfig /flushdns"
        os.system(command)
        time.sleep(1.5)

    elif selected_option == "n":
        os.system("cls" if os.name == "nt" else "clear")
        nics = get_all_nic_details()
        while True:
            print(header + "\n")
            print("-----------------------------------------------" + "\n")
            for i, nic in enumerate(nics):
                print(f"  {i + 1}. {nic['name']}")
            print("\n  C. Cancel")
            print("\n" + "-----------------------------------------------" + "\n")
            option = input("\x1b[36;49;1m  Your choice:\x1b[0m ")
            option = convert_keystrokes_fa_to_en(option).lower()

            if option == "c":
                break

            if option.isdigit():
                number = int(option)
                if number >= 1 and number <= len(nics):
                    target_nic_name = nics[number - 1]["name"]
                    save_config()
                    break

            print("  \x1b[37;41;1mInvalid input. Please try again...\x1b[0m")
            time.sleep(1.5)
            os.system("cls" if os.name == "nt" else "clear")

    elif selected_option == "u":
        os.system("cls" if os.name == "nt" else "clear")
        Update_check_result = check_Update()
        if Update_check_result == True:
            while True:
                print(header + "\n")
                print("-----------------------------------------------" + "\n")
                print(
                    "  Your current version is not up to date, do you want to Update now?"
                    + "\n"
                )
                print("    Y = YES")
                print("    N = NO")
                print("\n" + "-----------------------------------------------" + "\n")
                option = input("\x1b[36;49;1m  Your choice:\x1b[0m ")
                option = convert_keystrokes_fa_to_en(option).lower()

                if option == "y":
                    print()
                    if updater(file_name):
                        exit()
                    else:
                        print(
                            "  \x1b[37;41;1mFailed to download the latest version. Check your connection and try again\x1b[0m"
                        )
                        time.sleep(2)

                elif option == "n":
                    print("ok")
                    break

                else:
                    print("  \x1b[37;41;1mInvalid input. Please try again...\x1b[0m")
                    time.sleep(1.5)
                    os.system("cls" if os.name == "nt" else "clear")
        elif Update_check_result == False:
            print(header + "\n")
            print("-----------------------------------------------" + "\n")
            print("  You are using latest version.")
            time.sleep(2)
        else:
            print(header + "\n")
            print("-----------------------------------------------" + "\n")
            print(
                "  \x1b[37;41;1mUpdate check has failed please try again later.\x1b[0m"
            )
            time.sleep(2)

    else:
        # Invalid input
        print("  \x1b[37;41;1mInvalid input. Please try again...\x1b[0m")
        time.sleep(1.5)
