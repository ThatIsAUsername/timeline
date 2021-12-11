import sys
from collections import namedtuple

import pygame
from pygame_manager import PyGameManager as pgm
from pygame.locals import *

import color


def draw_screen():
    pygame.display.update()
    screen = pgm.get_screen()
    screen.fill(color.WHITE)
    screen_dims = screen.get_size()
    font = pgm.get_font()
    antialias = False
    dims_text = font.render(str(screen_dims), antialias, color.BLACK)
    screen.blit(dims_text, (10, 10))


def run():
    pgm.initialize()


    running = True
    while running:

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                running = False
            # if event.type == MOUSEBUTTONUP:
            #     mousex, mousey = event.pos
            #     if play_rect.collidepoint(mousex, mousey):
            #         choose_board()

        draw_screen()

    pgm.terminate()


if __name__ == "__main__":
    run()
