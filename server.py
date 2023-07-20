import threading
import socket
import time
import random
import argparse

MIN_CLIENT_COUNT = 2
MAX_CLIENT_COUNT = 4

client_count = 0
clients = []
game_end = False

# Handles the client during the game and executes game logic
def game_thread(server):
    # TODO
    pass

# Handles the connection of the client
def client_thread(server, connection, address):
    global client_count, clients
    print(f"New client connected {connection} with address {address}")

    # Send $id to the client
    connection.send(bytes(f"your id is {client_count - 1}", "utf-8"))

    # Notify all other clients that new client just connected
    for (c, a) in clients:
        if a != address:
            c.send(bytes(f"connected {client_count - 1}", "utf-8"))

    while True:
        # Listen to get the code
        code = (connection.recv(1024)).decode()

        if code == "start":
            if client_count >= MIN_CLIENT_COUNT:
                for (c, _) in clients:
                    c.send(bytes(f"start 1"))
                    threading._start_new_thread(game_thread, (server))
            else:
                for (c, _) in clients:
                    c.send(bytes(f"start 0"))


def main():
    global client_count, clients, game_end

    parser = argparse.ArgumentParser(description="Snakes and Ladders Server")
    parser.add_argument("-host", action="store", help="Host IP")
    parser.add_argument("-port", action="store",
                        help="Host TCP Port", type=int)

    args = parser.parse_args()

    # Checking if all inputs are provided
    if args.host == None or args.port == None:
        print("ERROR: Both host address and port should be specified")
        return

    print(f"Starting the server on host {args.host} on port {args.port}\n")

    # Binding the socket and listening
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((args.host, args.port))
    server.listen(MAX_CLIENT_COUNT)

    print("Waiting for clients to connect\n")

    # Flag that indicates whether MIN_CLIENT_COUNT has not been reached yet
    first_flag = True

    while not game_end:

        if client_count < MAX_CLIENT_COUNT:
            # Accept the connection and modify global client data
            connection, address = server.accept()
            client_count += 1
            clients.append((connection, address))

            # Start the thread for the client handling
            threading._start_new_thread(client_thread, (server, connection, address))

        # If the required client count has been reached for the first time, notify the clients
        if client_count >= MIN_CLIENT_COUNT and first_flag:
            for (c, _) in clients:
                c.send(bytes("ready to start", "utf-8"))
            first_flag = False


if __name__ == "__main__":
    main()
