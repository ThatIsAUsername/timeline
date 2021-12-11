
import pygame
from pygame.locals import *


class PyGameManager:
    font = None
    screen = None

    @staticmethod
    def initialize():
        pygame.init()

    @staticmethod
    def terminate():
        pygame.quit()

    @staticmethod
    def get_screen() -> pygame.Surface:
        if not PyGameManager.screen:
            screen_dims = (640, 480)
            PyGameManager.screen = pygame.display.set_mode(screen_dims, RESIZABLE)
        return PyGameManager.screen

    @staticmethod
    def get_font():
        if not PyGameManager.font:
            print('Creating font')
            PyGameManager.font = pygame.font.Font('freesansbold.ttf', 16)
        return PyGameManager.font
