import pygame
import socket
width = 1200
height = 800

pygame.init()

window = pygame.display.set_mode((width, height))

bg = pygame.image.load('BoardImage.png')
bg = pygame.transform.scale(bg,(width,height))

pygame.display.set_caption("Client")

clientNumber = 0

class Player():
    def __init__(self, x, y, width, height, colour):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.colour = colour
        self.rect = (x,y,width, height)

    def draw (self, win):
        pygame.draw.rect(window, self.colour, self.rect)

    #use to move. Should have way to tell if moving onto next row
    def move(self, size):
        self.x += size


def redrawWindow(window,player):
    #window.fill((255,255,255))
    player.draw(window)
    pygame.display.update()

def main():

    running = True
    p = Player(25,680,100,100,(255,0,0))


    while running:
        window.fill((0,0,0))
        window.blit(bg, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()

        p.move(40)
        redrawWindow(window, p)



main()