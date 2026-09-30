import socket
import psutil
print("====NETWORK INFORMATION====")
hostname=socket.gethostname()
print("Host Name : ",hostname)
ip_address=socket.gethostbyname(hostname)
print("IP_Address : ",ip_address)
print("\n====NETWORK INTERFACES====")
interfaces=psutil.net_if_addrs()
for interface,addresses in interfaces.items():
    print("\n Interfaces : ",interface)
    for add in addresses:
        print("Address : ",add.address)

