# Adapted from: https://realpython.com/python-sockets/

# echo-client.py

import socket

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 8088  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    while True:
        data = s.recv(1024)
        print(f"Received: {data.decode()}\n")