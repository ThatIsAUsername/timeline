
import sys
from typing import List
import pygame
from pygame_manager import PyGameManager as pgm
from pygame.locals import *

from data_types import Timeline, Timeview, TimePoint
from algorithms import interpolate


def run(file_list: List[str] = None):
    file_list = file_list or ["data/examples.yaml"]
    pgm.initialize()
    fps_clock = pygame.time.Clock()

    timeline = Timeline()
    timeline.load_records(file_list)
    timeview = Timeview(timeline)

    drag_anchor = None

    running = True
    while running:

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                running = False
            elif event.type == MOUSEWHEEL:

                mx, my = pygame.mouse.get_pos()
                width, height = pgm.get_screen().get_size()
                focus_date_ordinal = interpolate(mx, (0, width), (timeview.min.ordinal(), timeview.max.ordinal()))
                focus_date_ordinal = round(focus_date_ordinal)
                focus_date = TimePoint.from_ordinal(focus_date_ordinal)
                wheel_forward = event.y > 0
                wheel_backward = event.y < 0
                if wheel_forward:
                    timeview.zoom_in(focus_date)
                if wheel_backward:
                    timeview.zoom_out(focus_date)
            elif event.type == MOUSEBUTTONDOWN:
                mousex, mousey = event.pos
                width, height = pgm.get_screen().get_size()
                anchor_ordinal = interpolate(mousex, (0, width),
                                             (timeview.min.ordinal(), timeview.max.ordinal()))
                drag_anchor = TimePoint.from_ordinal(int(anchor_ordinal))

            elif event.type == MOUSEBUTTONUP:
                drag_anchor = None
            elif event.type == MOUSEMOTION:
                if drag_anchor is not None:
                    mousex, mousey = event.pos

                    width, height = pgm.get_screen().get_size()
                    x_ordinal = interpolate(mousex, (0, width),
                                            (timeview.min.ordinal(), timeview.max.ordinal()))
                    x_time = TimePoint.from_ordinal(int(x_ordinal))
                    timeview.pan(drag_anchor - x_time)

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
    file_list = [a for a in sys.argv][1:]
    run(file_list)
