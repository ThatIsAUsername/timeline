
from typing import Tuple
from collections import namedtuple
import math

import pygame
from pygame_manager import PyGameManager as pgm
from pygame.locals import *

from datetime import date, timedelta

import color
from data_types import Timeline, Timeview


def interpolate(v: int, source_range: Tuple[int, int], dest_range: Tuple[int, int]):

    # Interpolate the value v from the source range into the destination range.
    s0, s1 = source_range
    d0, d1 = dest_range
    ratio = (v-s0)/(s1-s0)  # How far this value is in the source range on a scale of 0 to 1.
    answer = d0 + ratio*(d1-d0)  # Interpolated value in the destination range.
    return answer


def draw_timeview(surf: pygame.Surface, timeview: Timeview):
    width, height = surf.get_size()
    time_range: timedelta = timeview.max - timeview.min
    time_range_s = time_range.total_seconds()

    buffer_pct = 0.02
    buffer_px = int(width*buffer_pct)
    # buffer_s = time_range_s * buffer_pct  # Give a little leeway around the denoted view range.
    # buffer_delta = timedelta(seconds=buffer_s)
    # x_zero_time = timeview.min - buffer_delta
    # x_width_time = timeview.max + buffer_delta

    timeline_y = height / 2
    pygame.draw.line(surface=surf, color=color.BLACK, start_pos=(0, timeline_y), end_pos=(width, timeline_y))

    # Generate positions/rects for all timeline elements
    visible_records = timeview.get_visible()

    # Generate all of the labels to draw and figure out the horizontal extents of each EventRecord.
    LabelInfo = namedtuple("LabelInfo", "x_vals label_surf label_rect")
    label_infos = []
    font = pgm.get_font()
    timeview_range = (timeview.min.toordinal(), timeview.max.toordinal())
    screen_range = (buffer_px, width-buffer_px)
    for rec in visible_records:
        xss = 0 if rec.start.min == -math.inf else interpolate(rec.start.min.toordinal(), timeview_range, screen_range)
        xse = width if rec.start.max == math.inf else interpolate(rec.start.max.toordinal(), timeview_range, screen_range)
        xes = 0 if rec.end.min == -math.inf else interpolate(rec.end.min.toordinal(), timeview_range, screen_range)
        xee = width if rec.end.max == math.inf else interpolate(rec.end.max.toordinal(), timeview_range, screen_range)
        antialias = False  # render takes no keyword arguments.
        label_surf = font.render(rec.name, antialias, color.BLACK)
        label_rect = pygame.rect.Rect((0, 0), label_surf.get_size())
        label_rect.bottomleft = (xse, height/2-label_rect.height/2)  # Start by placing all labels just above the line.
        label_infos.append(LabelInfo(x_vals=[xss, xse, xes, xee], label_surf=label_surf, label_rect=label_rect))

    # Deconflict as needed to position each label.
    deconflicted_rects = []
    for li in label_infos:
        lr = li.label_rect
        count = 0
        while lr.collidelist(deconflicted_rects) is not -1 and count < 10:
            count += 1
            # Move lr up to try and avoid.
            lr.bottomleft = (lr.x, lr.y-lr.height*1.5)
        deconflicted_rects.append(lr)

        # Render
        # Two spokes to the timeline to demarcate the known time span (between start.max and end.min).
        xss, xse, xes, xee = li.x_vals
        pygame.draw.line(surface=surf,
                         color=color.BLACK,
                         start_pos=(xse, lr.y+lr.height*1.25),
                         end_pos=(xse, timeline_y))
        pygame.draw.line(surface=surf,
                         color=color.BLACK,
                         start_pos=(xes, lr.y+lr.height*1.25),
                         end_pos=(xes, timeline_y))

        # One line showing the full possible extent in time.
        pygame.draw.line(surface=surf,
                         color=color.BLACK,
                         start_pos=(xss, lr.y+lr.height*1.25),
                         end_pos=(xee, lr.y+lr.height*1.25))

        # EventRecord's name.
        surf.blit(li.label_surf, li.label_rect.topleft)


def draw_screen(timeview):
    pygame.display.update()
    screen = pgm.get_screen()
    screen.fill(color.WHITE)

    # Draw timeview
    draw_timeview(screen, timeview)

    # Draw current resolution
    screen_dims = screen.get_size()
    font = pgm.get_font()
    antialias = False  # render takes no keyword arguments.
    dims_text = font.render(str(screen_dims), antialias, color.BLACK)

    screen.blit(dims_text, (10, 10))


def run():
    pgm.initialize()

    timeline = Timeline()
    timeline.load_from_file("data/rev_war.yaml")
    timeview = Timeview(timeline)

    running = True
    while running:

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                running = False
            # if event.type == MOUSEBUTTONUP:
            #     mousex, mousey = event.pos
            #     if play_rect.collidepoint(mousex, mousey):
            #         choose_board()

        draw_screen(timeview)

    pgm.terminate()


if __name__ == "__main__":
    run()
