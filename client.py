import time

import pygame
import socket
#from Game import Game
width = 1200
height = 700
cell_size = 60
grid_size = 10
grid_Xmargin = (width-cell_size*grid_size)//2
grid_Ymargin = (height-cell_size*grid_size)//2


pygame.init()

window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Client")

# bg = pygame.image.load('BoardImage.png')
# bg = pygame.transform.scale(bg,(width,height))

bg = pygame.Surface((width, height))
bg.fill((255, 255, 255))

clientNumber = 0

class Player():
    def __init__(self, x: object, y: object, width: object, height: object, colour: object) -> object:
        self.x = x
        self.y = y
        self.img = pygame.image.load('blue.png')
        self.img = pygame.transform.scale(self.img,(25,50))
        self.width = width
        self.height = height
        self.colour = colour

        self.calculate_screen_position()

    def calculate_screen_position(self):
        self.screen_x = grid_Xmargin + self.x * cell_size + cell_size //2 - self.width // 2
        self.screen_y = height - grid_Ymargin - self.y*cell_size - cell_size //2  - self.height //2

    def draw (self, win):
        self.calculate_screen_position()
        window.blit(self.img, (self.screen_x, self.screen_y))

    #use to move. Move to next row when reaching the end
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
        

def draw_grid():
    for x in range(grid_Xmargin, width - grid_Xmargin, cell_size):
        for y in range(grid_Ymargin, height - grid_Ymargin, cell_size):
            pygame.draw.rect(bg, (0, 0, 0), (x, y, cell_size, cell_size), 1)

def redrawWindow(window,player):
    window.blit(bg, (0, 0))
    player.draw(window)
    pygame.display.update()

def main():

    running = True
    draw_grid()
    p = Player(0, 0, 25, 50, (255, 0, 0))
    


    while running:
        # window.fill((255,255,255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()

        p.move(1)           #move should be able to take number of blocks to go forward
        time.sleep(1)       #added sleep to test how far piece will go with each move
        redrawWindow(window, p)



main()