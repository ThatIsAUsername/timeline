
import pygame
from pygame.locals import *


class PyGameManager:
    def __init__(self):
        self.font = None
        self.screen = None

    @staticmethod
    def initialize():
        pygame.init()

    @staticmethod
    def terminate():
        pygame.quit()

    def get_screen(self) -> pygame.Surface:
        if not self.screen:
            screen_dims = (640, 480)
            self.screen = pygame.display.set_mode(screen_dims, RESIZABLE)
        return self.screen

    def get_font(self) -> pygame.font.Font:
        if not self.font:
            print('Creating font')
            self.font = pygame.font.Font('freesansbold.ttf', 16)
        return self.font
