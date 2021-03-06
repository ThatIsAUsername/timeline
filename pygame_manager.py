
import pygame
from pygame.locals import *

from logs import get_logger


class PyGameManager:
    fonts = {}
    screen = None

    @staticmethod
    def initialize():
        pygame.init()
        PyGameManager.get_screen()  # Init a screen so we have one.

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
    def get_font(size: int = 12):
        if size not in PyGameManager.fonts:
            logger = get_logger()
            logger.debug(f'Creating font size {size}')
            font = pygame.font.Font('freesansbold.ttf', size)
            PyGameManager.fonts[size] = font
        return PyGameManager.fonts[size]
