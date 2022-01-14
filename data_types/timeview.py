
import math
from typing import List, Union
from collections import namedtuple

import pygame
from pygame_manager import PyGameManager as pgm
import color

from datetime import date, timedelta
import data_types
from algorithms import interpolate


class Timeview:

    # Determines how much to adjust the view when zooming.
    # Values must be [0-1], where lower numbers cause more change.
    ZOOM_RATIO = 0.8

    def __init__(self, timeline: data_types.Timeline):
        self.timeline = timeline
        self.min: date = self.timeline.min
        self.max: date = self.timeline.max
        self.render_min = data_types.SlidingValue(self.min.toordinal())
        self.render_max = data_types.SlidingValue(self.max.toordinal())

    def contains(self, timelike: Union[date, data_types.TimeReference, data_types.EventRecord]) -> bool:
        if type(timelike) is date:
            return self.contains_date(timelike)
        elif type(timelike) is data_types.TimeReference:
            return self.contains_reference(timelike)
        elif type(timelike) is data_types.EventRecord:
            return self.contains_record(timelike)

    def contains_date(self, d: date) -> bool:
        """
        Determine whether the date `d` is currently visible to the Timeview.
        Args:
            d: A date to compare

        Returns:
            True if `d` falls within the Timeview's purview, false otherwise.
        """
        return self.min <= d <= self.max

    def contains_reference(self, tr: data_types.TimeReference) -> bool:
        """
        Determine whether the given time reference is visible to the Timeview
        Args:
            tr: A normalized TimeReference (min and max must not be None).

        Returns:
            True if the TimeReference should be visible in this Timeview, false otherwise.
        """
        if type(tr.max) is date and tr.max < self.min \
                or type(tr.min) is date and tr.min > self.max:
            return False

        return True

    def contains_record(self, rec: data_types.EventRecord) -> bool:
        """
        Determine whether the provided EventRecord is visible to this Timeview.
        Args:
            rec: A normalized EventRecord

        Returns:
            True if the EventRecord would be at least partly visible within this Timeview, else False.
        """
        return self.contains_reference(rec.start) or self.contains_reference(rec.end)

    def get_visible(self) -> List[data_types.EventRecord]:
        """
        Returns:
            A list of all records from this view's Timeline that are also currently within the view.
        """
        visible_records = []
        for rec in self.timeline.get_records().values():
            if self.contains(rec):
                visible_records.append(rec)
        return visible_records

    def zoom_in(self, focus: date) -> None:
        """
        Changes the view's min and/or max to narrow the view on the provided date.
        Args:
            focus: The date to zoom in towards.

        Returns:
            None
        """
        assert self.contains(focus), "Cannot zoom on a date outside the view"

        min_ord = self.min.toordinal()
        max_ord = self.max.toordinal()
        foc_ord = focus.toordinal()

        lo_shift = timedelta((foc_ord - min_ord) * (1-self.ZOOM_RATIO))
        hi_shift = timedelta((max_ord - foc_ord) * (1-self.ZOOM_RATIO))

        self.min = self.min + lo_shift
        self.max = self.max - hi_shift
        self.render_min.set(self.min.toordinal())
        self.render_max.set(self.max.toordinal())

    def zoom_out(self, focus: date) -> None:
        """
        Changes the view's min and/or max to widen the view around the provided date.
        Args:
            focus: The date to zoom out from.

        Returns:
            None
        """
        assert self.contains(focus), "Cannot zoom on a date outside the view"

        min_ord = self.min.toordinal()
        max_ord = self.max.toordinal()
        foc_ord = focus.toordinal()

        zoom_frac = 1/(1-self.ZOOM_RATIO)
        lo_shift = timedelta((foc_ord - min_ord) * (1-self.ZOOM_RATIO))
        hi_shift = timedelta((max_ord - foc_ord) * (1-self.ZOOM_RATIO))

        try:
            self.min = self.min - hi_shift
        except OverflowError as oe:
            print("Warning! Attempting to view past the beginning of time!")
        try:
            self.max = self.max + lo_shift
        except OverflowError as oe:
            print("Warning! Attempting to view past the end of time!")
        self.render_min.set(self.min.toordinal())
        self.render_max.set(self.max.toordinal())

    def pan(self, delta: timedelta) -> None:
        """
        Shift the view by the prescribed delta.

        Args:
            delta: The amount to shift both the min and max bounds of the view.

        Returns:
            None
        """
        try:
            self.min = self.min + delta
        except OverflowError as oe:
            print("Warning! Attempting to pan view past the beginning of time!")

        try:
            self.max = self.max + delta
        except OverflowError as oe:
            print("Warning! Attempting to pan view past the end of time!")

        self.render_min.set(self.min.toordinal())
        self.render_max.set(self.max.toordinal())

    def render(self, surf: pygame.Surface):

        # First draw the background
        surf.fill(color.WHITE)

        min_ord = self.render_min.get()
        max_ord = self.render_max.get()
        timeview_range = (min_ord, max_ord)

        width, height = surf.get_size()

        buffer_pct = 0.02
        buffer_px = int(width*buffer_pct)
        # buffer_s = time_range_s * buffer_pct  # Give a little leeway around the denoted view range.
        # buffer_delta = timedelta(seconds=buffer_s)
        screen_range = (buffer_px, width-buffer_px)

        font = pgm.get_font()

        # Figure out where to draw guidelines. Then draw them.
        guidelines = self.generate_guidelines(self.min, self.max)
        for gl in guidelines:
            glx = interpolate(gl.toordinal(), timeview_range, screen_range)
            pygame.draw.line(surface=surf, color=color.LIGHT_GRAY, start_pos=(glx, 0), end_pos=(glx, height))
            antialias = True
            text = font.render(str(gl.year), antialias, color.LIGHT_GRAY)
            text_size = text.get_size()
            surf.blit(text, (glx+5, 5))
            surf.blit(text, (glx+5, height - text_size[1] - 5))


        timeline_y = height / 2
        pygame.draw.line(surface=surf, color=color.BLACK, start_pos=(0, timeline_y), end_pos=(width, timeline_y))

        # Generate positions/rects for all timeline elements
        visible_records = self.get_visible()

        # Generate all drawable labels and figure out the horizontal extents of each EventRecord.
        LabelInfo = namedtuple("LabelInfo", "x_vals label_surf label_rect")
        label_infos = []
        for rec in visible_records:
            xss = 0 if rec.start.min == -math.inf else interpolate(rec.start.min.toordinal(), timeview_range, screen_range)
            xse = width if rec.start.max == math.inf else interpolate(rec.start.max.toordinal(), timeview_range, screen_range)
            xes = 0 if rec.end.min == -math.inf else interpolate(rec.end.min.toordinal(), timeview_range, screen_range)
            xee = width if rec.end.max == math.inf else interpolate(rec.end.max.toordinal(), timeview_range, screen_range)
            antialias = True  # render takes no keyword arguments.
            label_surf = font.render(rec.name, antialias, color.BLACK)
            label_rect = pygame.rect.Rect((0, 0), label_surf.get_size())
            label_rect.bottomleft = (xse, height/2-label_rect.height/2)  # Start by placing all labels just above the line.
            label_infos.append(LabelInfo(x_vals=[xss, xse, xes, xee], label_surf=label_surf, label_rect=label_rect))

        # Deconflict as needed to position each label.
        deconflicted_rects = []
        for li in label_infos:
            lr = li.label_rect
            count = 0
            while lr.collidelist(deconflicted_rects) != -1 and count < 10:
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

            # Draw current resolution
            font = pgm.get_font()
            antialias = True  # render takes no keyword arguments.
            dims_text = font.render(str((width, height)), antialias, color.BLACK)

            surf.blit(dims_text, (10, 10))

    @staticmethod
    def generate_guidelines(min_date: date, max_date: date) -> List[date]:
        """
        Figure out where to draw guidelines to help orient the viewer.

        Args:
            min_date: The beginning of the visible time range.
            max_date: The end of the visible time range.

        Returns:
            A list of dates within the given range at which to draw orientation guidelines.
        """

        # Choose guidelines to show to always/usually show at least one, but not too many.
        # 0<span<1 - show no guidelines
        # 1<span<5 - show all years
        # 5<span<10 - show even-numbered years
        # 10<span<50 - show every 10
        # 50<span<100 - show every 50
        # <100 - every 100
        span = max_date.year - min_date.year
        mod = 1 if 0 < span <= 5 else \
            2 if 5 < span <= 10 else \
            10 if 10 < span <= 50 else \
            50 if 50 < span <= 100 else \
            100

        # Use the mod to find the specific dates to draw
        # Note that The max date's year should be visible; the min date's year may not.
        chosen_dates = []
        for year in range(min_date.year+1, max_date.year+1):
            if year % mod == 0:
                chosen_dates.append(date(year=year, month=1, day=1))
        return chosen_dates
