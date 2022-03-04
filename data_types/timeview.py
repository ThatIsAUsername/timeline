
import math
from random import randrange
from typing import List, Union
from collections import namedtuple

import pygame
from pygame_manager import PyGameManager as pgm
import color

from datetime import timedelta
import data_types
from algorithms import interpolate

TimePoint = data_types.TimePoint

# Utility struct to hold info about the event records we are drawing.
LabelInfo = namedtuple("LabelInfo", "id x_vals label_surf label_rect")


class Timeview:

    # Determines how much to adjust the view when zooming.
    # Values must be [0-1], where lower numbers cause more change.
    ZOOM_RATIO = 0.8

    def __init__(self, timeline: data_types.Timeline):
        self.timeline = timeline
        self.min: TimePoint = self.timeline.min
        self.max: TimePoint = self.timeline.max

        # The view is redrawn based on whether it has changed. So. Make sure it changes to begin.
        self.render_min = data_types.SlidingValue(self.max.ordinal())
        self.render_max = data_types.SlidingValue(self.min.ordinal())
        self.render_min.set(self.min.ordinal())
        self.render_max.set(self.max.ordinal())

        # Store the drawable information to avoid recalculating every frame.
        self.guidelines = []
        self.label_infos: List[LabelInfo] = []

        # Generate colors for each of the records.
        self.record_colors = {}
        for rec_id in self.timeline.get_records().keys():
            fg = pygame.Color(0)
            bg = pygame.Color(0)
            hue = randrange(0, 360)
            fg.hsva = (hue, 30, 90)
            bg.hsva = (hue, 50, 90, 0)
            self.record_colors[rec_id] = (fg, bg)

    def contains(self, timelike: Union[data_types.TimePoint, data_types.TimeReference, data_types.EventRecord]) -> bool:
        if type(timelike) is TimePoint:
            return self.contains_date(timelike)
        elif type(timelike) is data_types.TimeReference:
            return self.contains_reference(timelike)
        elif type(timelike) is data_types.EventRecord:
            return self.contains_record(timelike)

    def contains_date(self, d: TimePoint) -> bool:
        """
        Determine whether the date `d` is currently visible to the Timeview.
        Args:
            d: A TimePoint to compare

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
        if type(tr.max) is TimePoint and tr.max < self.min \
                or type(tr.min) is TimePoint and tr.min > self.max:
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

        contains_rec = self.contains_reference(rec.start) or self.contains_reference(rec.end)
        if contains_rec:
            return contains_rec

        # We may be zoomed inside the record such that the start and
        # end are not in view, but we still want to draw the record.
        if type(rec.start.min) is TimePoint and rec.start.min > self.max \
                or type(rec.end.max) is TimePoint and rec.end.max < self.min:
            return False
        return True

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

    def zoom_in(self, focus: TimePoint) -> None:
        """
        Changes the view's min and/or max to narrow the view on the provided TimePoint.
        Args:
            focus: The TimePoint to zoom in towards.

        Returns:
            None
        """
        assert self.contains(focus), "Cannot zoom on a date outside the view"

        min_ord = self.min.ordinal()
        max_ord = self.max.ordinal()
        foc_ord = focus.ordinal()

        lo_shift = timedelta((foc_ord - min_ord) * (1-self.ZOOM_RATIO))
        hi_shift = timedelta((max_ord - foc_ord) * (1-self.ZOOM_RATIO))

        self.min = self.min + lo_shift
        self.max = self.max - hi_shift
        self.render_min.set(self.min.ordinal())
        self.render_max.set(self.max.ordinal())

    def zoom_out(self, focus: TimePoint) -> None:
        """
        Changes the view's min and/or max to widen the view around the provided TimePoint.
        Args:
            focus: The TimePoint to zoom out from.

        Returns:
            None
        """
        assert self.contains(focus), "Cannot zoom on a date outside the view"

        min_ord = self.min.ordinal()
        max_ord = self.max.ordinal()
        foc_ord = focus.ordinal()

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
        self.render_min.set(self.min.ordinal())
        self.render_max.set(self.max.ordinal())

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

        self.render_min.set(self.min.ordinal())
        self.render_max.set(self.max.ordinal())

    def render(self, surf: pygame.Surface):

        regen_view = not self.render_min.is_at_destination() or not self.render_max.is_at_destination()

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
        if regen_view:
            self.guidelines = self.generate_guidelines(self.min, self.max)
        for gl in self.guidelines:
            glx = interpolate(gl.ordinal(), timeview_range, screen_range)
            pygame.draw.line(surface=surf, color=color.LIGHT_GRAY, start_pos=(glx, 0), end_pos=(glx, height))
            antialias = True
            text = font.render(str(gl.year), antialias, color.LIGHT_GRAY)
            text_size = text.get_size()
            surf.blit(text, (glx+5, 5))
            surf.blit(text, (glx+5, height - text_size[1] - 5))

        timeline_y = height / 2

        # Regenerate the drawable time events if the view changed.
        if regen_view:
            # Generate positions/rects for all timeline elements
            visible_records = self.get_visible()

            # Generate all drawable labels and figure out the horizontal extents of each EventRecord.
            self.label_infos = []
            for rec in visible_records:
                xss = -10 if rec.start.min == -math.inf else interpolate(rec.start.min.ordinal(), timeview_range, screen_range)
                xse = width if rec.start.max == math.inf else interpolate(rec.start.max.ordinal(), timeview_range, screen_range)
                xes = -10 if rec.end.min == -math.inf else interpolate(rec.end.min.ordinal(), timeview_range, screen_range)
                xee = width+10 if rec.end.max == math.inf else interpolate(rec.end.max.ordinal(), timeview_range, screen_range)
                antialias = True  # render takes no keyword arguments.
                label_surf = font.render(rec.name, antialias, color.BLACK)
                lw, lh = label_surf.get_size()
                label_rect = pygame.rect.Rect((0, 0), (xee-xss, lh+4))  # build a rect around the whole rendered record.
                label_rect.midleft = (xss, height/2)  # Start by horizontally centering all labels.
                label_rect.width = max(label_rect.width, label_surf.get_size()[0])
                self.label_infos.append(LabelInfo(id=rec.id, x_vals=[xss, xse, xes, xee], label_surf=label_surf, label_rect=label_rect))

            # Deconflict as needed to position each label.
            deconflicted_rects = []
            deconflict_up = False
            for li in self.label_infos:
                deconflict_up = not deconflict_up
                lr = li.label_rect
                count = 0
                idx = lr.collidelist(deconflicted_rects)
                while idx != -1 and count < 10:
                    count += 1

                    # Find the rect we are hitting and move past it.
                    other: pygame.Rect = deconflicted_rects[idx]
                    if deconflict_up:
                        lr.bottom = other.top
                    else:
                        lr.top = other.bottom
                    idx = lr.collidelist(deconflicted_rects)
                deconflicted_rects.append(lr)

        for li in self.label_infos:
            # Render
            # Draw an outline showing the full possible extent in time (start.min to end.max)
            lr = li.label_rect
            fgc, bgc = self.record_colors[li.id]
            xss, xse, xes, xee = li.x_vals
            pygame.draw.rect(surface=surf,
                             color=fgc,
                             rect=(xss, lr.top, xee-xss, lr.height),
                             border_radius=int(lr.height/2),
                             width=2
                             )

            # Draw a filled area showing the time during which the event was occurring (start.max to end.min).
            if xse <= xes:
                pygame.draw.rect(surface=surf,
                                 color=bgc,
                                 rect=(xse, lr.top, xes-xse, lr.height),
                                 border_radius=int(lr.height/2),
                                 # width=1
                                 )

            # EventRecord's name.
            label_buffer = 5
            label_x = xse if xse <= xes else xss
            # Ensure the label is drawn on-screen.
            label_x = label_buffer + label_x if label_x > 0 else label_buffer
            surf.blit(li.label_surf, (label_x, li.label_rect.y+2))

    @staticmethod
    def generate_guidelines(min_date: TimePoint, max_date: TimePoint) -> List[TimePoint]:
        """
        Figure out where to draw guidelines to help orient the viewer.

        Args:
            min_date: The beginning of the visible time range.
            max_date: The end of the visible time range.

        Returns:
            A list of TimePoints within the given range at which to draw orientation guidelines.
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
                chosen_dates.append(TimePoint(year=year, month=1, day=1))
        return chosen_dates
