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
turn_order = []
turn_order_count = 0

# TODO: create board 
def create_board():
    pass

def establish_turn_order():
    order = []
    for c in clients:
        order.append(c[1][1])
    random.shuffle(order)
    return order

# Computes the path of client based on the dice roll
# TODO: compute_path should keep track of clients position 
# and the server should know which position correspond to what
# this function should also determine if the game has ended or not
def compute_path(client_id, code):
    global clients
    for c in clients:
        if c[1][1] == client_id:
            # TODO: Update position
            pass
    pass

# Handles the client during the game and executes game logic
def game_thread(server, connection, address):
    global turn_order_count
    print(f"Game thread {address} has started")
    print(f"Turn order: {turn_order} {turn_order_count}")

    for c in clients:
        print(f"Client {type(c)}\n")

    while True:
        code = (connection.recv(1024)).decode()

        # computes and sends the path and turn packet in format of 
        # "path {client address} {path in array}"
        # "turn {client address}"
        if "dice" in code:
            path = compute_path(address[1], code)
            
            if turn_order_count == len(turn_order) - 1:
                turn_order_count = 0
            else:
                turn_order_count += 1

            for (con, _, _) in clients:
                con.send(bytes(f"path {address[1]} {path} {code}", "utf-8"))
                con.send(bytes(f"turn {turn_order[turn_order_count]}", "utf-8"))

# Handles the connection of the client
def client_thread(server, connection, address):
    global turn_order
    print(f"New client connected {connection} with address {address}")

    # Send $id to the client
    connection.send(bytes(f"your id is {client_count - 1}", "utf-8"))

    # Notify all other clients that new client just connected
    for (con, addr, _) in clients:
        if addr != address:
            con.send(bytes(f"connected {client_count - 1}", "utf-8"))

    while True:
        # Listen to get the code
        code = (connection.recv(1024)).decode()

        if code == "start":
            if client_count >= MIN_CLIENT_COUNT:
                # establishes the turn order before game start
                turn_order = establish_turn_order()
                for (con, addr, _) in clients:
                    con.send(bytes("start 1", "utf-8"))
                    con.send(bytes(f"turn {turn_order[turn_order_count]}", "utf-8"))
                    threading._start_new_thread(game_thread, (server, con, addr))
            else:
                for (con, _, _) in clients:
                    con.send(bytes("start 0", "utf-8"))


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
            clients.append([connection, address, (0,0)])

            # Start the thread for the client handling
            threading._start_new_thread(client_thread, (server, connection, address))

        # If the required client count has been reached for the first time, notify the clients
        if client_count >= MIN_CLIENT_COUNT and first_flag:
            for (con, _, _) in clients:
                con.send(bytes("ready to start", "utf-8"))
            first_flag = False


if __name__ == "__main__":
    main()
