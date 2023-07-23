import time
import select
import pygame
import socket
import random 

HOST = '127.0.0.1'
PORT = 8088  # The port used by the server

win_width = 1200
win_height = 700
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
board = pygame.image.load('BoardImage.png')
diceImaages = [pygame.image.load("dice1.png"), pygame.image.load("dice2.png"), pygame.image.load("dice3.png"),
               pygame.image.load("dice4.png"), pygame.image.load("dice5.png"), pygame.image.load("dice6.png")]
board = pygame.transform.scale(board,(win_width, win_height))

blue = pygame.transform.scale(pygame.image.load('blue.png'), (40, 40))
green = pygame.transform.scale(pygame.image.load('green.png'), (40, 40))
purple = pygame.transform.scale(pygame.image.load('purple.png'), (40, 40))
yellow = pygame.transform.scale(pygame.image.load('yellow.png'), (40, 40))

client_id = None
clientNumber = 0

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


def assign_color(client_id):
    player_color = ["red", "yellow", "blue","green"]
    return player_color[client_id % 4]


def main():

    # connect to the socket 
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    # while client_id is None:
    data = client_socket.recv(1024).decode()
    if data.startswith("your id is "):
        client_id = int(data.split()[3])
        print(f"Connected to the server. Your player ID is: {client_id}")
        my_color = assign_color(client_id)
        print(f"Your colour is: {my_color}")


    # initialize game objects
    # player = [Player(0, 0, 250, 50, yellow), Player(0, 0, 200, 50, my_color)]
    # dice_button = DiceButton(win_width / 2 + boardSize - diceImaages[0].get_width(),
    #                         win_height / 2 - diceImaages[0].get_height(), diceImaages[0].get_width(), diceImaages[0].get_height())
    # join_button = Button(win_width // 2 - 50, win_height // 2 - 20, 100, 40, "Join")
    join_text = Text("Joined. Waiting for other players to join.", (win_width // 2, win_height // 2 - 100), (0, 0, 0))
    ready_text = Text("Players joined. Ready to start.", (win_width // 2, win_height // 2 - 100), (0, 0, 0))
    start_button = Button(win_width // 2 - 50, win_height // 2, 100, 40, "Start")
    # win_text = Text("You won!", (win_width // 2, win_height // 2 - 100), (0, 255, 0))
    # lose_text = Text("You lose", (win_width // 2, win_height // 2 - 100), (255, 0, 0))

    running = True
    game_state = 0   # game state for display

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if game_state == 0 and check_button_click(mouse_pos, start_button):
                    # TODO: Signal Server
                    # TODO: Logic to proceed to game state 1, 2, 3, 4, 5
                    game_state = 2
                    
        data = client_socket.receive()
                
        if data == "ready to start":
            print(f"Received: {data}\n")
            game_state = 1
        # if data == "start 1":
        # elif data == "start 0":
        #     print("Waiting for more players to join...")
        # elif data.startswith("turn"):
        #     turn = int(data.split()[1])
        #     if turn == client_id:
        #         print("It's your turn. Type 'roll' to roll the dice.")
        #     else:
        #         print(f"Player {turn} is rolling the dice...")
        # elif data.startswith("path"):
        #     path = data.split()[2:]
        #     print(f"Player {path[0]} moves: {', '.join(path[1:])}")
        # elif data.startswith("winner"):
        #     winner = int(data.split()[1])
        #     if winner == client_id:
        #         print("Congratulations! You won the game.")
        #     else:
        #         print(f"Player {winner} won the game.")
        #     break
        
        window.blit(bg, (0, 0))

        # joined, waiting for others
        if game_state == 0:
            join_text.draw(window)

        # Ready to start
        elif game_state == 1:
            ready_text.draw(window)
            start_button.draw()


    #     user_input = input("> ")

    #     if user_input.lower() == "roll" and data.startswith("turn") and int(data.split()[1]) == client_id:
    #         client_socket.send(bytes("dice", "utf-8"))
    #     elif user_input.lower() == "exit":
    #         break

    # finally:
    #     client_socket.close()

  
        # for event in pygame.event.get():
        #     if event.type == pygame.QUIT:
        #         running = False
        #         pygame.quit()

        # for event in pygame.event.get():
        #     if event.type == pygame.QUIT:
        #         running = False
        #         pygame.quit()

    # drawDice = DiceButton(win_width / 2 + boardSize - diceImaages[0].get_width(),
    #                         win_height / 2 - diceImaages[0].get_height(), diceImaages[0].get_width(), diceImaages[0].get_height())
    # while running:
  
    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             running = False
    #             pygame.quit()

    #         drawDice.handle_event(event) # Check if the dice button is pressed

    #         if event.type == pygame.MOUSEBUTTONDOWN:
    #             mouse_pos = pygame.mouse.get_pos()
    #             if game_state == 0 and check_button_click(mouse_pos, join_button):
    #                 # Signal Server to join the game
    #                 clientSocket.send("join")
    #                 # if the "connected" message from te client is in the response, proceed to game state 1
    #                 game_state = 1
    #             elif game_state == 2 and check_button_click(mouse_pos, start_button):
    #                 clientSocket.send("start")
    #                 game_state = 3
    #                 window.blit(board, (0, 0))
    #             elif game_state == 3 and check_button_click(mouse_pos, dice_button):
    #                     dice_button.roll_dice()

            
    #         for event in pygame.event.get():
    #             if event.type == pygame.MOUSEBUTTONDOWN:
    #                 mouse_pos = pygame.mouse.get_pos()
    #                 if check_button_click(mouse_pos, join_button):
    #                     # Signal Server to join the game
    #                     clientSocket.send("join")
    #                     # if the "connected" message from the client is in the response, proceed to game state 1
    #                     clientSocket.send("status")
    #                     game_state = 1

    #     # joined, waiting for others
    #     elif game_state == 1:
    #         window.blit(bg, (0, 0))
    #         join_text.draw(window)

    #         # Check if all the players have joined and if the gme is ready to start
    #         clientSocket.send("status")
    #         #if "ready to start" in response:
    #         game_state = 2

    #     # Ready to start
    #     elif game_state == 2:
    #         window.blit(bg, (0, 0))
    #         ready_text.draw(window)
    #         start_button.draw()

    #     # in game
    #     elif game_state == 3:
    #         window.blit(board, (0, 0))
    #         drawDice.draw_dice()
    #         for p in player:
    #             p.draw(window)
    #             time.sleep(1)         # added sleep to test how far piece will go with each move
    #             p.move(1)             # move should be able to take number of blocks to go forward
    #         redrawWindow(window, player, drawDice, game_state)

    #     # win screen
    #     elif game_state == 4:
    #         window.blit(bg, (0, 0))
    #         win_text.draw(window)
        
    #     # lose screen
    #     elif game_state == 5:
    #         window.blit(bg, (0, 0))
    #         lose_text.draw(window)
        
        pygame.display.update()

if __name__ == "__main__":
    main()