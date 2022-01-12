
import pygame
from pygame_manager import PyGameManager as pgm
from pygame.locals import *

from datetime import date

from data_types import Timeline, Timeview
from algorithms import interpolate


def run():
    pgm.initialize()
    fps_clock = pygame.time.Clock()

    timeline = Timeline()
    timeline.load_from_file("data/rev_war.yaml")
    timeview = Timeview(timeline)

    running = True
    while running:

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                running = False
            if event.type == MOUSEWHEEL:

                mx, my = pygame.mouse.get_pos()
                width, height = pgm.get_screen().get_size()
                focus_date_ordinal = interpolate(mx, (0, width), (timeview.min.toordinal(), timeview.max.toordinal()))
                focus_date_ordinal = round(focus_date_ordinal)
                focus_date = date.fromordinal(focus_date_ordinal)
                wheel_forward = event.y > 0
                wheel_backward = event.y < 0
                if wheel_forward:
                    timeview.zoom_in(focus_date)
                if wheel_backward:
                    timeview.zoom_out(focus_date)
            # if event.type == MOUSEBUTTONUP:
            #     mousex, mousey = event.pos
            #     if play_rect.collidepoint(mousex, mousey):
            #         choose_board()

        surf = pgm.get_screen()
        timeview.render(surf)
        pygame.display.update()
        fps_clock.tick(60)

    pgm.terminate()


if __name__ == "__main__":
    run()
