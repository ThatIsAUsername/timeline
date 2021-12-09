import sys
from collections import namedtuple

import pygame
from pygame.locals import *

import color

Dimensions = namedtuple('dimensions', 'width height')


def initialize():
    pygame.init()


def terminate():
    pygame.quit()
    sys.exit()


def draw_screen(screen):
    pygame.display.update()
    pygame.draw.line(screen, color.BLACK, (0, 10), (20, 20))


def run():
    initialize()

    screen_dims = (640, 480)
    screen = pygame.display.set_mode(screen_dims, RESIZABLE)

    running = True
    while running:

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                running = False
            elif event.type == VIDEORESIZE or event.type == VIDEOEXPOSE:
                screen.fill(color.WHITE)  # handles window resize/minimize/maximize
            # if event.type == MOUSEBUTTONUP:
            #     mousex, mousey = event.pos
            #     if play_rect.collidepoint(mousex, mousey):
            #         choose_board()

        draw_screen(screen)

    terminate()


if __name__ == "__main__":
    run()
