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
turn_order_current = 0
snakes = {16: 6, 47: 26, 49: 11, 56: 53, 62: 19, 64: 60, 87: 24, 93: 73, 95: 75, 98: 78}
ladders = {1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 36: 44, 51: 67, 71: 91, 80: 100}

# Establishes the turn order for the game by randomizing client id
def establish_turn_order():
    order = []
    for i in range(len(clients)):
        order.append(i)
    random.shuffle(order)
    return order

# Computes the path of the player based on dice roll
#
# Params:
#   client_id: id of the client
#   code: code sent by the client
def compute_path(client_id, code):
    global clients
    dice_num = int(code.split()[1])
    path = []

    # increments the position and updates the path
    for i in range(dice_num):
        if clients[client_id][2] == 100:
            break
        path.append(clients[client_id][2] + 1)
        clients[client_id][2] += 1

    # check if the position landed is on a snake or ladder
    if clients[client_id][2] in snakes:
        clients[client_id][2] = snakes[clients[client_id][2]]
        path.append(clients[client_id][2])
    elif clients[client_id][2] in ladders:
        clients[client_id][2] = ladders[clients[client_id][2]]
        path.append(clients[client_id][2])

    return path



# Handles the client during the game and executes game logic
#
# Params: 
#   server: server socket
#   connection: connection socket
#   address: address of the client
def game_thread(server, connection, address):
    global turn_order_current
    print(f"Game thread {address} has started\n")
    print(f"Turn order: {turn_order}\n")

    while True:
        code = (connection.recv(1024)).decode()

        if "dice" in code:
            # compute the path and send it to all clients
            # if the client reaches 100, send winner packet to all clients
            path = compute_path(turn_order_current, code)
            if path[-1] == 100:
                for (con, _, _) in clients:
                    con.send(bytes(f"path {turn_order[turn_order_current]} {path}\n", "utf-8"))
                    con.send(bytes(f"winner {turn_order[turn_order_current]}\n", "utf-8"))
                game_end = True
                break
            
            if turn_order_current == len(turn_order) - 1:
                turn_order_current = 0
            else:
                turn_order_current += 1

            # sends the path of the player to all clients and the turn of the next client
            for (con, _, _) in clients:
                con.send(bytes(f"path {turn_order[turn_order_current - 1]} {path}\n", "utf-8"))
                con.send(bytes(f"turn {turn_order[turn_order_current]}\n", "utf-8"))

# Handles the connection of the client
#
# Params: 
#   server: server socket
#   connection: connection socket
#   address: address of the client
def client_thread(server, connection, address):
    global turn_order
    print(f"New client connected {connection} with address {address}")

    # Send $id to the client
    connection.send(bytes(f"your id is {client_count - 1}\n", "utf-8"))

    # Notify all other clients that new client just connected
    for (con, addr, _) in clients:
        if addr != address:
            con.send(bytes(f"connected {client_count - 1}\n", "utf-8"))

    while True:
        # Listen to get the code
        code = (connection.recv(1024)).decode()

        if code == "start":
            if client_count >= MIN_CLIENT_COUNT:
                # establishes the turn order before game start
                turn_order = establish_turn_order()
                for (con, addr, _) in clients:
                    con.send(bytes("start 1\n", "utf-8"))
                    con.send(bytes(f"turn {turn_order[turn_order_current]}\n", "utf-8"))
                    threading._start_new_thread(game_thread, (server, con, addr))
            else:
                for (con, _, _) in clients:
                    con.send(bytes("start 0\n", "utf-8"))


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
            
            # client array should include connection, address, and position
            clients.append([connection, address, 0])
            
            for (i, (_, _, _)) in enumerate(clients[:-1]):
                connection.send(bytes(f"connected {i}\n", "utf-8"))
            
            if not first_flag:
                connection.send(bytes(f"ready to start\n", "utf-8"))
            

            # Start the thread for the client handling
            threading._start_new_thread(client_thread, (server, connection, address))

        # If the required client count has been reached for the first time, notify the clients
        if client_count >= MIN_CLIENT_COUNT and first_flag:
            for (con, _, _) in clients:
                con.send(bytes("ready to start\n", "utf-8"))
            first_flag = False


if __name__ == "__main__":
    main()
