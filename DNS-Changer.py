import subprocess
import os
import pyuac
import ctypes
import time

#Run as admin
if not ctypes.windll.shell32.IsUserAnAdmin():
        # Re-launch the script with elevated privileges
        pyuac.runAsAdmin()


header = ( '''\x1b[92;1m     __        __           ___ ___ 
\ / /  \ |  | |__)    |\ | |__   |  
 |  \__/ \__/ |  \    | \| |___  |  
                                    
                     __   ___  __  
|\/|  /\  |\ |  /\  / _` |__  |__) 
|  | /~~\ | \| /~~\ \__> |___ |  \ 
                                   \x1b[0m''' + "\n" + " Khosh oomadi:")

Bye = ('''\x1b[36;49;1m
     _             _         
    / `_  _   _/  /_)   _   /
   /_;/_//_//_/  /_)/_//_' . 
                    _/       
\x1b[0m''')


def get_interface_name():
    output = subprocess.check_output(['netsh', 'interface','ipv4', 'show', 'interface'])
    output = output.decode('utf-8')

    for line in output.split('\n'):
        if ('Connected' and '1500') in line:
            iface = line.split()[4]
            return iface
    
    return ('\x1b[37;41;1mNo Adapter Found !!!\x1b[0m')

#Checks what DNS is set on connection adapter.
def DNS_Check(adapter_name):
        
    # Run the 'ipconfig' command and capture its output
    output = subprocess.check_output(['ipconfig', '/all'])

    # Convert the output to a string
    output_str = output.decode('utf-8')

    # Check if DHCP Server is equal to DNS Server for the specified adapter.
    if f"{adapter_name}:" in output_str and 'DNS Servers . . . . . . . . . . . :' in output_str.split(f"{adapter_name}:")[1]:
        dns_servers = [line.strip().split(": ")[1] for line in output_str.split(f"{adapter_name}:")[1].split("\n") if "DNS Servers" in line]
        dhcp_server = [line.strip().split(": ")[1] for line in output_str.split(f"{adapter_name}:")[1].split("\n") if "DHCP Server" in line][0]
        if len(dns_servers) == 1 and dns_servers[0] == dhcp_server:
            return(f'\x1b[34;1mOh! DNS Server Not set for\x1b[0m {adapter_name}')
        else:
            if ("178.22.122.100" and "185.51.200.2") in output_str:
                return(f'\x1b[32;1mYes! Shecan DNS Server is set for\x1b[0m {adapter_name}')
            
            elif ("1.1.1.1" and "1.0.0.1") in output_str:
                return(f'\x1b[32;1mYes! Cloudflare DNS Server is set for\x1b[0m {adapter_name}')
            
            elif ("8.8.8.8" and "8.8.4.4") in output_str:
                return(f'\x1b[32;1mYes! Google DNS Server is set for\x1b[0m {adapter_name}')

            elif ("10.202.10.202" and "10.202.10.102") in output_str:
                return(f'\x1b[32;1mYes! 403 DNS Server is set for\x1b[0m {adapter_name}')
            
            elif ("10.202.10.10" and "10.202.10.11") in output_str:
                return(f'\x1b[32;1mYes! RadarGame DNS Server is set for\x1b[0m {adapter_name}')
            
            else:
                return(f'\x1b[33;1mUnknown DNS is set for\x1b[0m {adapter_name}')
    else:
        return(f'Oops!!! No DNS found for {adapter_name}')


#DNSs
DNSs = {
    "Shecan": ['178.22.122.100', '185.51.200.2'],
    "Cloudflare":['1.1.1.1', '1.0.0.1'],
    "Google":['8.8.8.8', '8.8.4.4'],
    "403":['10.202.10.202', '10.202.10.102'],
    "RadarGame":['10.202.10.10', '10.202.10.11']
}
selected_option = None


#Sets DNS.
def Set_DNS(DNSserver):
    preferred_dns = DNSs[DNSserver][0]
    alternate_dns = DNSs[DNSserver][1]

    output = subprocess.check_output(['netsh', 'interface', 'show', 'interface'])
    output = output.decode('utf-8')
    for line in output.split('\n'):
        if ('connected' and '1500') in line:
            face = line.split()[-1]
            print("Your Internet Connection Adapter is: " + face)
            break  # assuming there is only one connected interface

    # Set the preferred DNS server
    if os.system(f'netsh interface ip set dns name="{Name}" static {preferred_dns}') == 0:
        print('\x1b[92;1mPreferred DNS server set successfully\x1b[0m')
        time.sleep(1)
    else:
        print('\x1b[31;1mError setting preferred DNS server\x1b[0m')
        time.sleep(1)
    # Add the alternate DNS server
    if os.system(f'netsh interface ip add dns name="{Name}" {alternate_dns} index=2') == 0:
        print('\x1b[92;1mAlternate DNS server added successfully\x1b[0m')
        time.sleep(1)
    else:
        print('\x1b[31;1mError adding alternate DNS server\x1b[0m')
        time.sleep(1)

#Main process runs here.
while selected_option != "q":
    # Clear the console screen
    os.system("cls" if os.name == "nt" else "clear")
    
    # Print the header text with the current options
    print(header + ("\n"))
    Name = get_interface_name()
    DNS_Status = DNS_Check(Name)
    print(f' Adapter name ==> \x1b[33;1m{Name}\x1b[0m')
    print(" " + DNS_Status)
    print("-----------------------------------------------"+"\n")
    for i, DNS in enumerate(DNSs):
        print("  {}. {}".format(i+1, DNS))
    print("  D. Disable DNS")
    print("  Q. Exit")
    print("\n"+"-----------------------------------------------"+"\n")

    selected_option = input("\x1b[36;49;1m  Your choice:\x1b[0m ")
    
    if selected_option.isdigit() and int(selected_option) <= len(DNSs):
        # Do something for the selected option
        Choosen = (int(selected_option) - 1)
        Selected_DNS = list(DNSs.keys())[Choosen]
        print("You selected: {}".format(Selected_DNS))
        Set_DNS(Selected_DNS)


    elif selected_option == "q":
        # Exit the loop
        os.system("cls" if os.name == "nt" else "clear")
        print(Bye)
        time.sleep(2)


    elif selected_option == "d":
        # Define the command to remove DNS from the network adapter
        command = f'netsh interface ipv4 delete dns "{Name}" all'

        # Execute the command using subprocess
        subprocess.call(command, shell=True)
        print("\x1b[35;47;1mDNS successfuly disabled.\x1b[0m")
        time.sleep(1.5)
    else:
        # Invalid input
        print("\x1b[37;41;1mInvalid input. Please try again...\x1b[0m")
        time.sleep(1.5)






