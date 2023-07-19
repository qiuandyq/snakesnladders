import time
import pygame
import socket
import threading
#from Game import Game
width = 1200
height = 800

pygame.init()

window = pygame.display.set_mode((width, height))

bg = pygame.image.load('BoardImage.png')
bg = pygame.transform.scale(bg,(width,height))

pygame.display.set_caption("Client")

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

    def draw (self, win):
        window.blit(self.img, (self.x, self.y))

    #use to move. Should have way to tell if moving onto next row
    def move(self, size):
        self.x += (size*55)         #wanted to make it go to next block each time

class Socket:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = socket.gethostbyname(socket.gethostname())
        self.port = 8888
        self.address = (self.server, self.port)
        self.score = self.connect()

    def getPosition(self):
        return self.score
    
    def connect(self):
        try:
            self.client.connect(self.address)
        except:
            pass 
    
    def send(self, data):
        try:
            lock = threading.Lock()
            with lock:
                self.client.send(str.encode(data))
                return self.client.recv(4096).decode()
        except socket.error as e:
            print(e)


def redrawWindow(window,player, sock):
    #window.fill((255,255,255))
    player.draw(window)
    pygame.display.update()

def main():

    running = True
    p = Player(215,680,100,100,(255,0,0))


    while running:
        window.fill((0,0,0))
        window.blit(bg, (0, 0))
        sock = Socket()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()

        p.move(1)           #move should be able to take number of blocks to go forward
        time.sleep(1)       #added sleep to test how far piece will go with each move
        redrawWindow(window, p, sock)



main()
