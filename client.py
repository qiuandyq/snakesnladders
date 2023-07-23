import time
import select
import pygame
import socket
import random 
import argparse
import threading
import queue
# python3 client.py -host localhost -port 8088

client_id = None
client_count = 0

win_width = 500
win_height = 300
boardSize = 500
cell_size = 60
grid_size = 10
grid_Xmargin = (win_width-cell_size*grid_size)//2
grid_Ymargin = (win_height-cell_size*grid_size)//2

pygame.init()
window = pygame.display.set_mode((win_width, win_height))
pygame.display.set_caption("Snakes and Ladders")

bg = pygame.Surface((win_width, win_height))
bg.fill((255, 255, 255))

class Socket:
    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.address = (self.host, self.port)
        self.connected = False
        self.message_queue = queue.Queue()  # Create a queue for received messages
        self.client_id_lock = threading.Lock()  # Create a lock for client_id
        self.running = True
        self.buffer = ""

    def connect(self):
        try:
            self.client.connect(self.address)
            self.connected = True
        except socket.error as e:
            print("Connection error: ", e)
            self.connected = False

    def receive(self):
        self.client.settimeout(0.1)  # Set a timeout of 0.1 seconds for receiving data
        try:
            data = self.client.recv(1024).decode()
            if not data:
                return None

            self.buffer += data
            messages = self.buffer.split("\n")
            self.buffer = messages[-1]  # Save any incomplete message to be handled later
            messages = messages[:-1]  # Remove the incomplete message from the list

            return messages
        except socket.timeout:
            return None
    
    def receive_messages(self):
        while self.running:  # Add a flag to control the loop
            messages = self.receive()
            if messages:
                for message in messages:
                    self.message_queue.put(message)
                    print(f"Received: {message}")

    def send(self, data):
        try:
            self.client.sendall(str.encode(data))
        except socket.error as e:
            print("Socket error: ", e)

    def close(self):
        self.client.close()
        self.connected = False
        self.running = False


class Text:
    def __init__(self, text, position, color, font_size=30):
        self.text = text
        self.position = position
        self.color = color
        self.font_size = font_size
        self.font = pygame.font.Font(None, self.font_size)

    def draw(self, window):
        text_surface = self.font.render(self.text, True, self.color)
        text_rect = text_surface.get_rect(center=self.position)
        window.blit(text_surface, text_rect)


class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text

    def draw(self):
        pygame.draw.rect(window, (0, 0, 0), self.rect, 2)
        font = pygame.font.SysFont(None, 40)
        text_render = font.render(self.text, True, (0, 0, 0))
        text_rect = text_render.get_rect(center=self.rect.center)
        window.blit(text_render, text_rect)


def check_button_click(mouse_pos, button):
    return button.rect.collidepoint(mouse_pos)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Snakes and Ladders Client")
    parser.add_argument("-host", action="store", help="Host IP")
    parser.add_argument("-port", action="store", help="Host TCP Port", type=int)
    args = parser.parse_args()

    if args.host is None or args.port is None:
        print("Please provide both host address and port.")

    socket_client = Socket(args.host, args.port)
    socket_client.connect()

    game_state = 0 

    # inialize game objects
    join_text = Text("Joined. Waiting for other players to join.", (win_width // 2, win_height // 2 - 100), (0, 0, 0))
    ready_text = Text("Players joined. Ready to start.", (win_width // 2, win_height // 2 - 100), (0, 0, 0))
    start_button = Button(win_width // 2 - 50, win_height // 2, 100, 40, "Start")

    message_thread = threading.Thread(target=socket_client.receive_messages)
    message_thread.daemon = True
    message_thread.start()

    client_id_lock = threading.Lock()

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if game_state == 1 and check_button_click(mouse_pos, start_button):
                        # TODO: Logic to proceed to game state 1, 2, 3, 4, 5
                        game_state = 2
                        # TODO: Signal Server

            while not socket_client.message_queue.empty():
                data = socket_client.message_queue.get()
                # Process the received data here (e.g., check for "your id is ", "ready to start", etc.)
                if data is not None:
                    if data.startswith("your id is "):
                        with socket_client.client_id_lock:  # Use the lock to protect client_id
                            client_id = int(data.split()[3])
                            client_count += 1
                            print(f"Connected to the server. Your player ID is: {client_id}")
                    elif data == "ready to start":
                        print(f"Received: {data}\n")
                        game_state = 1
                    elif data.startswith("connected "):
                        client_count = int(data.split()[1]) + 1
                        print(f"{client_count} players joined.")

            window.blit(bg, (0, 0))

            # joined, waiting for others
            if game_state == 0:
                join_text.draw(window)

            # Ready to start
            elif game_state == 1:
                ready_text.draw(window)
                start_button.draw()
                # else:
                #     # Connection closed by the server or an error occurred
                #     break

            pygame.display.update()
            
    finally:
        socket_client.close()
