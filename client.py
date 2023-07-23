import time
import select
import pygame
import socket
import random 
import argparse
import threading
import queue

client_id = None
client_count = 0

win_width = 1200
win_height = 700
boardSize = 500
cell_size = 60
grid_size = 10
grid_Xmargin = (win_width-cell_size*grid_size)//2
grid_Ymargin = (win_height-cell_size*grid_size)//2

pygame.init()

window = pygame.display.set_mode((win_width, win_height))
pygame.display.set_caption("Client")

bg = pygame.Surface((win_width, win_height))
bg.fill((255, 255, 255))

board = pygame.image.load('BoardImage.png')
diceImaages = [pygame.image.load("dice1.png"), pygame.image.load("dice2.png"), pygame.image.load("dice3.png"),
               pygame.image.load("dice4.png"), pygame.image.load("dice5.png"), pygame.image.load("dice6.png")]
board = pygame.transform.scale(board,(win_width, win_height))

blue = pygame.transform.scale(pygame.image.load('blue.png'), (40, 40))
green = pygame.transform.scale(pygame.image.load('green.png'), (40, 40))
purple = pygame.transform.scale(pygame.image.load('purple.png'), (40, 40))
yellow = pygame.transform.scale(pygame.image.load('yellow.png'), (40, 40))

clientNumber = 0

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
            print("Connectio error: ", e)
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

class Player():
    def __init__(self, x, y, width, height, colour):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.colour = colour
        self.img = self.get_player_img(colour)
    
    def get_player_img(self, colour):
        if colour == yellow:
            return yellow
        elif colour == green:
            return green
        elif colour == blue:
            return blue
        elif colour == purple:
            return purple
        

    def calculate_screen_position(self):
        self.screen_x = grid_Xmargin + self.x * \
            cell_size + cell_size // 2 - self.width // 2
        self.screen_y = win_height - grid_Ymargin - self.y * \
            cell_size - cell_size // 2 - self.height // 2

    def draw(self, window):
        self.calculate_screen_position()
        window.blit(self.img, (self.screen_x, self.screen_y))

    # use to move. Move to next row when reaching the end
    def move(self, size):
        if self.y % 2 == 0:  # Even y-coordinate (move right)
            if self.x + size <= grid_size-1:
                self.x += 1
            else:
                self.y += 1
        else:  # Odd y-coordinate (move left)
            if self.x - size >= 0:
                self.x -= size
            else:
                self.y += 1
        
        self.calculate_screen_position() # Calculate the screen posotion for each player after each move

class DiceButton:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.dice_images = diceImaages
        self.current_dice = random.randint(1, 6)

    def draw_dice(self):
        #pygame.draw.rect(window, (0, 0, 0), self.rect, 2)
        window.blit(self.dice_images[self.current_dice - 1], (win_width / 2 + boardSize - diceImaages[0].get_width(),
                                                  win_height / 2 - diceImaages[0].get_height()))

    def roll_dice(self):
        self.current_dice = random.randint(1, 6)
        self.draw_dice() 

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                self.roll_dice()

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


def draw_grid():
    for x in range(grid_Xmargin, win_width - grid_Xmargin, cell_size):
        for y in range(grid_Ymargin, win_height - grid_Ymargin, cell_size):
            pygame.draw.rect(bg, (0, 0, 0), (x, y, cell_size, cell_size), 1)


def get_coordinates_from_position(position):
    row = grid_size - 1 - (position - 1) // grid_size
    col = (position - 1) % grid_size

    x = grid_Xmargin + col * cell_size + cell_size // 2
    y = win_height - (grid_Ymargin + row * cell_size) - cell_size // 2

    return x, y

def redrawWindow(window, players, dice, game_state):
    window.blit(board, (0, 0))
    pygame.draw.rect(bg, (0, 0, 0), (grid_Xmargin, grid_Ymargin, cell_size * grid_size, cell_size * grid_size), 2)
    
    for player in players:
        player.draw(window)

    dice.draw_dice()

    pygame.display.update()

running = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Snakes and Ladders Client")
    parser.add_argument("-host", action="store", help="Host IP")
    parser.add_argument("-port", action="store", help="Host TCP Port", type=int)
    args = parser.parse_args()

    if args.host is None or args.port is None:
        print("Please provide both host address and port.")

    socket_client = Socket(args.host, args.port)
    socket_client.connect()

    game_state = 0   # game state for display

    player1 = Player(0, 0, 250, 50, yellow)
    player2 = Player(0, 0, 200, 50, green)

    dice_button = DiceButton(win_width / 2 + boardSize - diceImaages[0].get_width(),
                            win_height / 2 - diceImaages[0].get_height(), diceImaages[0].get_width(), diceImaages[0].get_height())
    join_button = Button(win_width // 2 - 50, win_height // 2 - 20, 100, 40, "Join")
    join_text = Text("Joined. Waiting for other players to join.", (win_width // 2, win_height // 2 - 100), (0, 0, 0))
    ready_text = Text("Players joined. Ready to start.", (win_width // 2, win_height // 2 - 100), (0, 0, 0))
    start_button = Button(win_width // 2 - 50, win_height // 2, 100, 40, "Start")
    win_text = Text("You won!", (win_width // 2, win_height // 2 - 100), (0, 255, 0))
    lose_text = Text("You lose", (win_width // 2, win_height // 2 - 100), (255, 0, 0))

    drawDice = DiceButton(win_width / 2 + boardSize - diceImaages[0].get_width(),
                            win_height / 2 - diceImaages[0].get_height(), diceImaages[0].get_width(), diceImaages[0].get_height())

    message_thread = threading.Thread(target=socket_client.receive_messages)
    message_thread.daemon = True
    message_thread.start()

    client_id_lock = threading.Lock()

    currentPlayer = 1 

    try:
        while running:
    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()

                drawDice.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if game_state == 0 and check_button_click(mouse_pos, join_button):
                        # Signal Server to join the game
                        socket_client.send("join")
                        # if the "connected" message from te client is in the response, proceed to game state 1
                        game_state = 1
                    elif game_state == 2 and check_button_click(mouse_pos, start_button):
                        socket_client.send("start")
                        game_state = 3
                        window.blit(board, (0, 0))
                    elif game_state == 3 and check_button_click(mouse_pos, dice_button):
                            dice_button.roll_dice()


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

            # ready to join
            if game_state == 0:
                window.blit(bg, (0, 0))
                join_button.draw()
                
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        if check_button_click(mouse_pos, join_button):
                            # Signal Server to join the game
                            socket_client.send("join")
                            # if the "connected" message from the client is in the response, proceed to game state 1
                            socket_client.send("status")
                            game_state = 1

            # joined, waiting for others
            elif game_state == 1:
                window.blit(bg, (0, 0))
                join_text.draw(window)

                # Check if all the players have joined and if the gme is ready to start
                socket_client.send("status")
                #if "ready to start" in response:
                game_state = 2

            # Ready to start
            elif game_state == 2:
                window.blit(bg, (0, 0))
                ready_text.draw(window)
                start_button.draw()

            # in game
            elif game_state == 3:
                window.blit(board, (0, 0))
                drawDice.draw_dice()
                
                if currentPlayer == 1 and check_button_click(mouse_pos, dice_button):
                    dice_value = dice_button.current_dice
                    # moving Player 1 
                    if player1.x + player1.y < 100:
                        for _ in range(dice_value):
                            player1.move(1)    
                            redrawWindow(window, [player1, player2], drawDice, game_state)
                            pygame.time.delay(100) # move should be able to take number of blocks to go forward

                    if player2.x + player2.y < 100:
                        for _ in range(dice_value):
                            player2.move(1)    
                            redrawWindow(window, [player1, player2], drawDice, game_state)
                            pygame.time.delay(100) # move should be able to take number of blocks to go forward

                    # Check for which player wins 
                    if player1.x + player1.y >= 100:
                        game_state = 4
                    elif player2.x + player2.y >= 100:
                        game_state = 5

                redrawWindow(window, [player1, player2], drawDice, game_state)

            # win screen
            elif game_state == 4:
                window.blit(bg, (0, 0))
                win_text.draw(window)
            
            # lose screen
            elif game_state == 5:
                window.blit(bg, (0, 0))
                lose_text.draw(window)
            
            pygame.display.update()

    finally:
        socket_client.close()

