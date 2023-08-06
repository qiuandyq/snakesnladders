import threading
import socket
import time
import random
import argparse
# python3 server.py -host localhost -port 8088

MIN_CLIENT_COUNT = 2
MAX_CLIENT_COUNT = 4

client_count = 0
clients = []
addr_to_cid = {}
game_end = False
not_started = True
snakes = {16: 6, 47: 26, 49: 11, 56: 53, 62: 19, 64: 60, 87: 24, 93: 73, 95: 75, 98: 78}
ladders = {1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 36: 44, 51: 67, 71: 91, 80: 100}
dice_holder = -1
dice_lock = threading.Lock();

# Computes the path of the player based on dice roll
#
# Params:
#   client_id: id of the client
#   code: code sent by the client
def compute_path(client_id, code):
    global clients
    dice_num = int(code.split()[1])
    # print(f"Received: {code}")
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
    global dice_holder, game_end, dice_lock
    print(f"Game thread {address} has started\n")

    while True:
        if not dice_lock.locked():
            if game_end:
                return

            code = (connection.recv(1024)).decode()
            if code != None:
                print(f"Received: {code}")

            # first come first serve logic for taking the dice
            # if the dice is not being held, the client can take the dice
            # if the dice is being held, the client will be sent an error
            if code == "take":
                dice_lock.acquire()
                try:
                    if dice_holder == -1:
                        dice_holder = addr_to_cid[address]
                        for (con, _, _) in clients:
                            con.send(bytes(f"turn {dice_holder}\n", "utf-8"))
                    else:
                        print("Error message 2, take in code, dice_holder != -1")
                        connection.send(bytes(f"ERROR: client {dice_holder} is currently holding the dice\n", "utf-8"))
                finally:
                    dice_lock.release()

            # when the client rolls the dice, execute the game logic
            if "dice" in code:
                if dice_holder != addr_to_cid[address]:
                    print("Error Message 1, dice in code, dice_holder != addr_client " , dice_holder)
                    connection.send(bytes(f"ERROR: client {dice_holder} is currently holding the dice\n", "utf-8"))
                else:
                    # compute the path and send it to all clients
                    # if the client reaches 100, send winner packet to all clients
                    path = compute_path(dice_holder, code)
                    if path[-1] == 100:
                        for (con, _, _) in clients:
                            con.send(bytes(f"path {addr_to_cid[address]} {path}\n", "utf-8"))
                            if dice_holder == addr_to_cid[address]:
                                con.send(bytes(f"winner {addr_to_cid[address]}\n", "utf-8"))

                        game_end = True
                        break

                    for (con, _, _) in clients:
                        con.send(bytes(f"path {addr_to_cid[address]} {path}\n", "utf-8"))

            if "ready to take" in code:
                # sends the path of the player to all clients and the resets dice_holder to notify dice is up for grabs
                for (con, _, _) in clients:
                    dice_holder = -1
                    con.send(bytes(f"dice is up for grabs\n", "utf-8"))


# Handles the connection of the client
#
# Params: 
#   server: server socket
#   connection: connection socket
#   address: address of the client
def client_thread(server, connection, address):
    global game_end, not_started
    print(f"New client connected {connection} with address {address}")

    # Send $id to the client
    connection.send(bytes(f"your id is {client_count - 1}\n", "utf-8"))

    # Notify all other clients that new client just connected
    for (con, addr, _) in clients:
        if addr != address:
            con.send(bytes(f"connected {client_count - 1}\n", "utf-8"))

    
    while not_started:
        if game_end:
            return
        # Listen to get the code
        code = (connection.recv(1024)).decode()

        print(f"New code {code} in client thread")
        if code == "start":
            if client_count >= MIN_CLIENT_COUNT:
                for (con, addr, _) in clients:
                    con.send(bytes("start 1\n", "utf-8"))
                    threading._start_new_thread(game_thread, (server, con, addr))
                not_started = False
                
            else:
                for (con, _, _) in clients:
                    con.send(bytes("start 0\n", "utf-8"))
                    
    if game_end:
        return

    print(f"Client thread {address} quits")


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
    print(f'socket options: {server.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)}')
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f'socket options: {server.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)}')
    server.bind((args.host, args.port))
    server.listen(MAX_CLIENT_COUNT)

    print("Waiting for clients to connect\n")

    # Flag that indicates whether MIN_CLIENT_COUNT has not been reached yet
    first_flag = True

    while not game_end:
        if client_count < MAX_CLIENT_COUNT and not_started:
            print("New connection")
            # Accept the connection and modify global client data
            connection, address = server.accept()
            
            client_count += 1
            # maps address to client id
            addr_to_cid[address] = client_count - 1
            
            # client array should include connection, address, and position
            clients.append([connection, address, 0])
            
            for (i, (_, _, _)) in enumerate(clients[:-1]):
                connection.send(bytes(f"connected {i}\n", "utf-8"))
            
            if not first_flag:
                connection.send(bytes(f"ready to start\n", "utf-8"))
            

            # Start the thread for the client handling
            threading._start_new_thread(client_thread, (server, connection, address))
            print(f"clients: {addr_to_cid}")

        # If the required client count has been reached for the first time, notify the clients
        if client_count >= MIN_CLIENT_COUNT and first_flag:
            for (con, _, _) in clients:
                con.send(bytes("ready to start\n", "utf-8"))
            first_flag = False
        
    
    for (con, _, _) in clients:
        con.close()
    
    server.close()
    return


if __name__ == "__main__":
    main()
