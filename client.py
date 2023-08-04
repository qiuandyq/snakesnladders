import time
import pygame
import socket
import random
import argparse
import threading
import queue

# To run in terminal:
# python3 client.py -host localhost -port 8088

# TODO: some indicators of who is rolling
# TODO: some indicators of what color the player is
# TODO: some indicators of what number is rolled
# TODO: update game board with numbers and snake and ladders
# TODO: Fix the issue of needing multiple clicks on the dice to send the dice msg to server

client_id = None
client_count = 0
turn_current = None

win_width = 500
win_height = 300
boardSize = 500
cell_size = 26
grid_size = 10
grid_Xmargin = (win_width-cell_size*grid_size)//2
grid_Ymargin = (win_height-cell_size*grid_size)//2

pygame.init()
window = pygame.display.set_mode((win_width, win_height))
pygame.display.set_caption("Snakes and Ladders")

bg = pygame.Surface((win_width, win_height))
bg.fill((255, 255, 255))

red = pygame.transform.scale(
    pygame.image.load('assets/Player_red.png'), (14, 14))
blue = pygame.transform.scale(
    pygame.image.load('assets/Player_blue.png'), (14, 14))
green = pygame.transform.scale(
    pygame.image.load('assets/Player_green.png'), (14, 14))
yellow = pygame.transform.scale(
    pygame.image.load('assets/Player_yellow.png'), (14, 14))


class Socket:
    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.address = (self.host, self.port)
        self.connected = False
        self.message_queue = queue.Queue()  # Create a queue for received messages
        # self.client_id_lock = threading.Lock()  # Create a lock for client_id
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
        # Set a timeout of 0.1 seconds for receiving data
        self.client.settimeout(0.1)
        try:
            data = self.client.recv(1024).decode()
            if not data:
                return None

            self.buffer += data
            messages = self.buffer.split("\n")
            # Save any incomplete message to be handled later
            self.buffer = messages[-1]
            # Remove the incomplete message from the list
            messages = messages[:-1]

            return messages
        except socket.timeout:
            return None

    def receive_messages(self):
        while self.running:
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

    def is_my_turn(self, turn_current):
        # with self.client_id_lock:
            return client_id == turn_current


class Player():
    def __init__(self, x, y, width, height, colour):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.img = colour

    def calculate_screen_position(self):
        self.screen_x = grid_Xmargin + self.x * \
            cell_size + cell_size // 2 - self.width // 2
        self.screen_y = win_height - grid_Ymargin - self.y * \
            cell_size - cell_size // 2 - self.height // 2

    def draw(self, window):
        self.calculate_screen_position()
        window.blit(self.img, (self.screen_x, self.screen_y))

    def move(self, position):

        # Calculate the x-coordinate (0~9) and y-coordinate (0~9) based on board position
        self.y = position // 10
        if self.y % 2 == 0:
            if position % 10 != 0:
                self.x = position % 10 - 1
            else:
                self.x = 0
        else:
            if position % 10 != 0:
                self.x = 9-(position % 10 - 1)
            else:
                self.x = 9

        # Calculate the screen posotion for each player after each move
        self.calculate_screen_position()


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
        self.clickable = True

    def draw(self):
        color = (0, 0, 0) if self.clickable else (128, 128, 128)  # black if clickable, otherwise grey,
        pygame.draw.rect(window, color, self.rect, 2)
        font = pygame.font.SysFont(None, 40)
        text_render = font.render(self.text, True, color)
        text_rect = text_render.get_rect(center=self.rect.center)
        window.blit(text_render, text_rect)

    def set_clickable(self, value):
        self.clickable = value

    def check_button_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                print("Button clicked!")
                return True

        return False


class DiceButton(Button):
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

        # The dice images for both states
        self.dice_clickable_image = pygame.image.load("assets/dice1.png")
        self.dice_disabled_image = pygame.image.load(
            "assets/dice_disabled.png")

        # Resize the dice images to match the size of the button
        self.dice_clickable_image = pygame.transform.scale(
            self.dice_clickable_image, (width, height))
        self.dice_disabled_image = pygame.transform.scale(
            self.dice_disabled_image, (width, height))

        self.clickable = False

    def draw(self):
        if self.clickable:
            dice_image = self.dice_clickable_image
        else:
            dice_image = self.dice_disabled_image

        window.blit(dice_image, self.rect.topleft)

    def roll(self):
        if self.clickable:
            roll_result = random.randint(1, 6)
            print(f"Dice rolled: {roll_result}")
            return roll_result
        else:
            # The button is disabled, do nothing when clicked
            pass
    


def draw_grid():
    for x in range(grid_Xmargin, win_width - grid_Xmargin, cell_size):
        for y in range(grid_Ymargin, win_height - grid_Ymargin, cell_size):
            pygame.draw.rect(bg, (0, 0, 0), (x, y, cell_size, cell_size), 1)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Snakes and Ladders Client")
    parser.add_argument("-host", action="store", help="Host IP")
    parser.add_argument("-port", action="store",
                        help="Host TCP Port", type=int)
    args = parser.parse_args()

    if args.host is None or args.port is None:
        print("Please provide both host address and port.")

    socket_client = Socket(args.host, args.port)
    socket_client.connect()

    game_state = 0
    moving_player = None
    moves = []
    open_to_take = False

    # inialize game objects
    join_text = Text("Joined. Waiting for other players to join.",
                     (win_width // 2, win_height // 2 - 100), (0, 0, 0))
    ready_text = Text("Players joined. Ready to start.",
                      (win_width // 2, win_height // 2 - 100), (0, 0, 0))
    start_button = Button(win_width // 2 - 50,
                          win_height // 2, 100, 40, "Start")
    take_button = Button(win_width - grid_Xmargin,
                          win_height // 2, 100, 40, "Take")
    # take_button = DiceButton(win_width - grid_Xmargin,
    #                         win_height - grid_Ymargin-50, 50, 50)
    dice_button = DiceButton(win_width - grid_Xmargin,
                             win_height - grid_Ymargin-50, 50, 50)
    win_text = Text("You won!", (win_width // 2,
                    win_height // 2 - 100), (0, 255, 0))
    lose_text = Text("You lose", (win_width // 2,
                     win_height // 2 - 100), (255, 0, 0))

    player_0 = Player(-1, 0, 14, 14, red)
    player_1 = Player(-2, 0,  14, 14, blue)
    player_2 = Player(-1, 1,  14, 14, yellow)
    player_3 = Player(-2, 1,  14, 14, green)

    players = {
        0: player_0,
        1: player_1,
        2: player_2,
        3: player_3
    }

    message_thread = threading.Thread(target=socket_client.receive_messages)
    message_thread.daemon = True
    message_thread.start()

    # client_id_lock = threading.Lock()

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()

                if game_state == 1 and start_button.check_button_click(event):
                    socket_client.send("start")

                elif game_state == 2:
                    if take_button.clickable is True and take_button.check_button_click(event):
                        socket_client.send("take")
                        print("take message sent")
                    elif dice_button.clickable is True and dice_button.check_button_click(event):
                        socket_client.send(f"dice {dice_button.roll()}")
                        print("dice message sent")

            # TODO: Move this block to the Socket Class maybe
            while not socket_client.message_queue.empty():
                data = socket_client.message_queue.get()
                # Process the received data here (e.g., check for "your id is ", "ready to start", etc.)
                if data is not None:
                    if data.startswith("your id is "):
                        # with socket_client.client_id_lock:  # Use the lock to protect client_id
                            client_id = int(data.split()[3])
                            client_count = client_id + 1
                            print(
                                f"{client_count} Players connected to the server. Your player ID is: {client_id}")
                    elif data == "ready to start":
                        game_state = 1
                    elif data.startswith("connected "):
                        client_count = int(data.split()[1]) + 1
                        print(f"{client_count} players joined.")
                    elif data == "start 1":
                        game_state = 2
                        print(f"Game Started.")
                    elif data.startswith("turn "):
                        take_button.set_clickable(False)
                        turn_current = int(data.split()[1])
                        if socket_client.is_my_turn(turn_current):
                            dice_button.set_clickable(True)
                            print(f"It's my turn.")
                        else:
                            dice_button.set_clickable(False)
                            print(f"It's player {turn_current}'s turn.")
                    elif data.startswith("path "):
                        # Example format: "path 1 [1, 2]"
                        game_state = 3
                        dice_button.set_clickable(False)
                        take_button.set_clickable(False)
                        data_parts = data.split()
                        moving_player = int(data_parts[1])
                        moves_str = data[data.find("[")+1:data.find("]")]
                        moves = [int(move) for move in moves_str.split(",")]
                        print(
                            f"Received path for player {moving_player}: {moves}")
                    elif data == "dice is up for grabs":
                        take_button.set_clickable(True)

                    # TODO: Get win and lost msgs from server and decode
                    else:
                        pass

            # Update screen
            window.blit(bg, (0, 0))

            # joined, waiting for others
            if game_state == 0:
                join_text.draw(window)

            # Ready to start
            elif game_state == 1:
                ready_text.draw(window)
                start_button.draw()

            # In game: Compete for take
            elif game_state == 2:
                draw_grid()
                take_button.draw()
                dice_button.draw()

                for i in range(0, client_count):
                    players[i].draw(window)

            # In game: Moving players
            elif game_state == 3:
                draw_grid()
                take_button.draw()
                dice_button.draw()

                if moves:
                    # Remove the first element from the list
                    move = moves.pop(0)
                    players[moving_player].move(move)
                    time.sleep(1)
                else:
                    moving_player = None
                    game_state = 2
                    socket_client.send("ready to take")
                    socket_client.send("ready to take")
                    # if turn_current == client_id:
                    #     dice_button.set_clickable(True)
                    # else:
                    #     dice_button.set_clickable(False)

                for i in range(0, client_count):
                    players[i].draw(window)
            
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
