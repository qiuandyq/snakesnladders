import time

import pygame
import socket
# from Game import Game
win_width = 1200
win_height = 700
cell_size = 60
grid_size = 10
grid_Xmargin = (win_width-cell_size*grid_size)//2
grid_Ymargin = (win_height-cell_size*grid_size)//2


pygame.init()

window = pygame.display.set_mode((win_width, win_height))
pygame.display.set_caption("Client")

# bg = pygame.image.load('BoardImage.png')
# bg = pygame.transform.scale(bg,(width,height))

bg = pygame.Surface((win_width, win_height))
bg.fill((255, 255, 255))

clientNumber = 0


class Player():
    # TODO: change color based on the colour argument
    def __init__(self, x: object, y: object, width: object, height: object, colour: object) -> object:
        self.x = x
        self.y = y
        self.img = pygame.image.load('blue.png')
        self.img = pygame.transform.scale(self.img, (25, 50))
        self.width = width
        self.height = height
        self.colour = colour

    def calculate_screen_position(self):
        self.screen_x = grid_Xmargin + self.x * \
            cell_size + cell_size // 2 - self.width // 2
        self.screen_y = win_height - grid_Ymargin - self.y * \
            cell_size - cell_size // 2 - self.height // 2

    def draw(self, win):
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

    # TODO: another move function for snakes and ladders

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


# def redrawWindow(window, player, game_state):
#     window.blit(bg, (0, 0))
#     if game_state == 1:
#     draw_grid()
#     player.draw(window)
#     pygame.display.update()


def main():

    running = True
    game_state = 0   # game state for display

    # TODO: Get assgined colour from server
    # TODO: New class for dice
    p = Player(0, 0, 25, 50, (255, 0, 0))
    join_button = Button(win_width // 2 - 50, win_height // 2 - 20, 100, 40, "Join")
    join_text = Text("Joined. Waiting for other players to join.", (win_width // 2, win_height // 2 - 100), (0, 0, 0))
    ready_text = Text("x players joined. Ready to start.", (win_width // 2, win_height // 2 - 100), (0, 0, 0))
    start_button = Button(win_width // 2 - 50, win_height // 2, 100, 40, "Start")
    win_text = Text("You won!", (win_width // 2, win_height // 2 - 100), (0, 255, 0))
    lose_text = Text("You lose", (win_width // 2, win_height // 2 - 100), (255, 0, 0))

    while running:
        # window.fill((255,255,255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if game_state == 0 and check_button_click(mouse_pos, join_button):
                    # TODO: Signal Server
                    # TODO: Logic to proceed to game state 1, 2, 3, 4, 5
                    game_state = 1
        
        # window.fill((255,255,255))
        window.blit(bg, (0, 0))

        # ready to join
        if game_state == 0:
            join_button.draw()

        # joined, waiting for others
        elif game_state == 1:
            join_text.draw(window)

        # Ready to start
        elif game_state == 2:
            ready_text.draw(window)
            start_button.draw()

        # in game
        # TODO: Display other Player
        # TODO: Inicator of own color
        # TODO: Indicator of whose turn it is right now
        # TODO: Display Dice and its status (can roll/can't roll)
        # TODO: Logic to update movement based on msg from server
        elif game_state == 3:
            draw_grid()
            p.draw(window)
            time.sleep(1)         # added sleep to test how far piece will go with each move
            p.move(1)             # move should be able to take number of blocks to go forward
            # redrawWindow(window, p, game_state)

        # win screen
        elif game_state == 4:
            win_text.draw(window)
        
        # lose screen
        elif game_state == 5:
            lose_text.draw(window)

        pygame.display.update()


main()
