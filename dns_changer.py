import os
import sys
import time
import json
import pyuac
import ctypes
import threading

import updater
import network_adapters
from input_sanitizer import convert_keystrokes_fa_to_en
from dns_providers import DNS_PROVIDERS
from version import VERSION

CONFIG_FILE = "config.json"
target_nic_name = None
detected_nic_name = None


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


# Checks what DNS is set on a network interface.
def get_dns_status(nic_name):
    nics = network_adapters.get_all_nic_details()

    for nic in nics:
        if nic["name"] != nic_name:
            continue

        if (
            nic["dhcp_server"]
            and len(nic["dns_servers"]) == 1
            and nic["dns_servers"][0] == nic["dhcp_server"]
        ):
            return f"\x1b[34;1mOh! DNS Server Not set for\x1b[0m {nic_name}"

        if len(nic["dns_servers"]) > 1:
            for provider in DNS_PROVIDERS.keys():
                if (
                    DNS_PROVIDERS[provider][0] == nic["dns_servers"][0]
                    and DNS_PROVIDERS[provider][1] == nic["dns_servers"][1]
                ):
                    return f"\x1b[32;1mYes! {provider} DNS Server is set for\x1b[0m {nic_name}"

        return f"\x1b[33;1mUnknown DNS is set for\x1b[0m {nic_name}"

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


def main():
    # Run as admin
    if not ctypes.windll.shell32.IsUserAnAdmin():
        # Re-launch the script with elevated privileges
        pyuac.runAsAdmin()

    # set CMD window height and width
    os.system("mode 78,35")

    load_config()
    updater_thread = threading.Thread(target=updater.check_Update)
    updater_thread.start()

    # Main process runs here.
    while True:
        # Clear the console screen
        os.system("cls" if os.name == "nt" else "clear")

        exe_path = sys.argv[0]
        exe_filename = exe_path.split("\\")[-1]

        # Print the header text with the current options
        print(header + "\n")

        # Print DNS status of the network interface
        global target_nic_name
        if target_nic_name:  # User has selected a newtork interface
            nics = network_adapters.get_all_nic_details()
            target_nic_exists = False
            for nic in nics:
                if nic["name"] == target_nic_name:
                    target_nic_exists = True

            DNS_status = get_dns_status(target_nic_name)

            not_available_notification = "\x1b[37;41;1mNot Available!\x1b[0m"
            print(
                f" Selected network adapter ==> \x1b[33;1m{target_nic_name}\x1b[0m "
                + f"{'' if target_nic_exists else not_available_notification}"
            )
            print(" " + DNS_status)
            print("-----------------------------------------------" + "\n")

        else:  # User has not selected a newtork interface
            detected_nic_name = network_adapters.detect_default_network_interface()

            if detected_nic_name:
                DNS_status = get_dns_status(detected_nic_name)
                print(
                    f" Detected network adapter ==> \x1b[33;1m{detected_nic_name}\x1b[0m"
                )
                print(" " + DNS_status)
                print("-----------------------------------------------" + "\n")
            else:
                print(f" \x1b[37;41;1mCould not detect any connected adapter\x1b[0m")
                print()
                print("-----------------------------------------------" + "\n")

        nic_name = target_nic_name if target_nic_name else detected_nic_name

        # Print menu options
        for i, DNS in enumerate(DNS_PROVIDERS):
            print("  {}. {}".format(i + 1, DNS))
        print()
        print("  C. Clear DNS (auto)")
        print("  F. Flush DNS cache")
        print("  N. Choose network adapter")
        print()
        update_notification = "\x1b[38;5;119m(New version available)\x1b[0m"
        print(
            f"  U. Update {update_notification if updater.is_update_available else ''}"
        )
        print("  G. Github page")
        print("  Q. Quit")
        print("\n" + "-----------------------------------------------")

        selected_option = input("\x1b[36;49;1m  Your choice:\x1b[0m ")
        selected_option = convert_keystrokes_fa_to_en(selected_option).lower()
        print()

        if selected_option.isdigit() and int(selected_option) <= len(DNS_PROVIDERS):
            # Do something for the selected option
            chosen_dns_index = int(selected_option) - 1
            selected_DNS = list(DNS_PROVIDERS.keys())[chosen_dns_index]
            print("You selected: {}".format(selected_DNS))
            set_DNS(nic_name, selected_DNS)

        elif selected_option == "q":
            break

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
            nics = network_adapters.get_all_nic_details()
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
            update_check_result = updater.check_Update()
            if update_check_result == True:
                while True:
                    print(header + "\n")
                    print("-----------------------------------------------" + "\n")
                    print(
                        "  Your current version is not up to date, do you want to Update now?"
                        + "\n"
                    )
                    print("    Y = YES")
                    print("    N = NO")
                    print(
                        "\n" + "-----------------------------------------------" + "\n"
                    )
                    option = input("\x1b[36;49;1m  Your choice:\x1b[0m ")
                    option = convert_keystrokes_fa_to_en(option).lower()

                    if option == "y":
                        print()
                        if updater.update(exe_filename):
                            sys.exit()
                        else:
                            print(
                                "  \x1b[37;41;1mFailed to download the latest version. Check your connection and try again\x1b[0m"
                            )
                            time.sleep(2)
                            os.system("cls" if os.name == "nt" else "clear")

                    elif option == "n":
                        print("ok")
                        break

                    else:
                        print(
                            "  \x1b[37;41;1mInvalid input. Please try again...\x1b[0m"
                        )
                        time.sleep(1.5)
                        os.system("cls" if os.name == "nt" else "clear")
            elif update_check_result == False:
                print(header + "\n")
                print("-----------------------------------------------" + "\n")
                print("  You are using the latest version.")
                time.sleep(2)
            else:
                print(header + "\n")
                print("-----------------------------------------------" + "\n")
                print(
                    "  \x1b[37;41;1mUpdate check has failed please try again later.\x1b[0m"
                )
                time.sleep(2)
        elif selected_option == "g":
            os.system("start https://github.com/aedangaming/DNS-Changer")

        else:
            # Invalid input
            print("  \x1b[37;41;1mInvalid input. Please try again...\x1b[0m")
            time.sleep(1.5)


if __name__ == "__main__":
    main()
