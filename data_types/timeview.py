
import math
from random import randrange
from typing import List, Tuple, Union
from collections import namedtuple

import pygame
from pygame_manager import PyGameManager as pgm
import color

from datetime import timedelta
import data_types
from algorithms import interpolate
from logs import get_logger

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

        # Invert min/max for starting positions so we get a nice zoom effect on startup.
        self.render_min = data_types.SlidingValue(self.max.ordinal())
        self.render_max = data_types.SlidingValue(self.min.ordinal())

        # Set the target zoom to frame the records with a buffer on each side.
        min_ord = self.min.ordinal()
        max_ord = self.max.ordinal()
        framing_ratio = 0.02
        framing_ord = (max_ord-min_ord)*framing_ratio
        frame_min = min_ord - framing_ord
        frame_max = max_ord + framing_ord
        self.render_min.set(frame_min)
        self.render_max.set(frame_max)
        self.render_force = False

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

    def contains(self, timelike: Union[int, data_types.TimePoint, data_types.TimeReference, data_types.EventRecord]) -> bool:
        if type(timelike) is int:
            return self.min.ordinal() <= timelike <= self.max.ordinal()
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

    def zoom_in(self, focus: int) -> None:
        """
        Changes the view's min and/or max to narrow the view on the provided ordinal day.
        Args:
            focus: The ordinal day to zoom in towards.

        Returns:
            None
        """
        assert self.contains(focus), f"Cannot zoom on a day ({focus}) outside the view ({self.min.ordinal()}-{self.max.ordinal()})"

        min_ord = self.min.ordinal()
        max_ord = self.max.ordinal()

        lo_shift = timedelta((focus - min_ord) * (1-self.ZOOM_RATIO))
        hi_shift = timedelta((max_ord - focus) * (1-self.ZOOM_RATIO))

        self.min = self.min + lo_shift
        self.max = self.max - hi_shift
        self.render_min.set(self.min.ordinal())
        self.render_max.set(self.max.ordinal())

    def zoom_out(self, focus: int) -> None:
        """
        Changes the view's min and/or max to widen the view around the provided ordinal day.
        Args:
            focus: The ordinal of the date to zoom out from.

        Returns:
            None
        """
        assert self.contains(focus), f"Cannot zoom on a day ({focus}) outside the view ({self.min.ordinal()}-{self.max.ordinal()})"

        min_ord = self.min.ordinal()
        max_ord = self.max.ordinal()

        lo_shift = timedelta((focus - min_ord) * (1-self.ZOOM_RATIO))
        hi_shift = timedelta((max_ord - focus) * (1-self.ZOOM_RATIO))

        try:
            self.min = self.min - hi_shift
        except (ValueError, OverflowError) as oe:
            log = get_logger()
            log.warning(f"Attempting to view past the beginning of time! Details:\n  {str(oe)}")
        try:
            self.max = self.max + lo_shift
        except (ValueError, OverflowError) as oe:
            log = get_logger()
            log.warning(f"Attempting to view past the end of time! Details:\n  {str(oe)}")

        self.render_min.set(self.min.ordinal())
        self.render_max.set(self.max.ordinal())

    def pan(self, delta_days: int) -> None:
        """
        Shift the view by the prescribed delta.

        Args:
            delta_days: The number of days to shift both the min and max bounds of the view.

        Returns:
            None
        """
        try:
            self.min = self.min + timedelta(days=delta_days)
        except OverflowError:
            log = get_logger()
            log.warning(f"Attempting to pan view past the beginning of time!")

        try:
            self.max = self.max + timedelta(days=delta_days)
        except OverflowError:
            log = get_logger()
            log.warning(f"Attempting to pan view past the end of time!")

        self.render_min.set(self.min.ordinal())
        self.render_max.set(self.max.ordinal())

    def force_redraw(self):
        """
        The next call to render will regenerate the window unconditionally.
        """
        self.render_force = True

    def render(self, surf: pygame.Surface):

        regen_view = self.render_force or (not self.render_min.is_at_destination() or not self.render_max.is_at_destination())
        self.render_force = False

        # First draw the background
        surf.fill(color.WHITE)

        min_ord = self.render_min.get()
        max_ord = self.render_max.get()
        timeview_range = (min_ord, max_ord)

        width, height = surf.get_size()

        font = pgm.get_font()

        # Figure out where to draw guidelines. Then draw them.
        if regen_view:
            self.guidelines = self.generate_guidelines(self.min, self.max)
        for gl in self.guidelines:
            glx = interpolate(gl.ordinal(), timeview_range, (0, width))
            pygame.draw.line(surface=surf, color=color.LIGHT_GRAY, start_pos=(glx, 0), end_pos=(glx, height))
            antialias = True
            text = font.render(str(gl.year), antialias, color.LIGHT_GRAY)
            text_size = text.get_size()
            surf.blit(text, (glx+5, 5))
            surf.blit(text, (glx+5, height - text_size[1] - 5))

        # Regenerate the drawable time events if the view changed.
        if regen_view:
            # Generate positions/rects for all timeline elements
            visible_records = self.get_visible()
            self.calculate_record_positions(visible_records, width, height, timeview_range)

        for li in self.label_infos:
            # Render
            # Draw an outline showing the full possible extent in time (start.min to end.max)
            lr = li.label_rect
            fgc, bgc = self.record_colors[li.id]
            xss, xse, xes, xee = li.x_vals
            xspan = xee-xss
            line_width = 2 if xspan >= 4 else 1 if xspan >= 2 else 1
            if xspan > 1:
                pygame.draw.rect(surface=surf,
                             color=fgc,
                             rect=(xss, lr.top, xspan, lr.height),
                             border_radius=int(lr.height/2),
                             width=line_width
                             )
            else:  # Just draw a single 1-pixel line so it doesn't disappear entirely.
                pygame.draw.line(surface=surf, color=fgc, start_pos=(xss, lr.top), end_pos=(xss, lr.top+lr.height))

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
        if len(chosen_dates) > 20:  # Too many lines; view gets busy.
            desired_max = 10  # Ten is pretty reasonable to keep.
            skip = int(len(chosen_dates) / desired_max)
            new_dates = []
            for ii in range(0, len(chosen_dates), skip):
                new_dates.append(chosen_dates[ii])
            chosen_dates = new_dates

        return chosen_dates

    def calculate_record_positions(self,
                                   visible_records: List[data_types.EventRecord],
                                   window_width_px: int,
                                   window_height_px: int,
                                   timeview_range: Tuple[int, int],
                                   ):
        """
        Figure out where to draw all the records on the window.

        Args:
            visible_records: All records that are to be positioned. May be a subset or everything.
            screen_width_px: Current width of the drawable window in pixels.
            screen_height_px: Current height of the drawable window in pixels.
            timeview_range: Ordinal min/max values of the beginning/end of the visible timeline.
        """
        # Generate all drawable labels and figure out the horizontal extents of each EventRecord.
        self.label_infos = []
        for rec in visible_records:
            w_range = (0, window_width_px)
            xss = -10 if rec.start.min == -math.inf else interpolate(rec.start.min.ordinal(), timeview_range, w_range)
            xse = window_width_px+10 if rec.start.max == math.inf else interpolate(rec.start.max.ordinal(), timeview_range, w_range)
            xes = -10 if rec.end.min == -math.inf else interpolate(rec.end.min.ordinal(), timeview_range, w_range)
            xee = window_width_px+10 if rec.end.max == math.inf else interpolate(rec.end.max.ordinal(), timeview_range, w_range)
            antialias = True  # render takes no keyword arguments.
            label_surf = pgm.get_font().render(rec.name, antialias, color.BLACK)
            lw, lh = label_surf.get_size()
            label_rect = pygame.rect.Rect((0, 0), (xee-xss, lh+4))  # build a rect around the whole rendered record.
            label_rect.midleft = (xss, window_height_px/2)  # Start by vertically centering all labels.
            label_rect.width = max(label_rect.width, label_surf.get_size()[0])
            self.label_infos.append(LabelInfo(id=rec.id, x_vals=[xss, xse, xes, xee], label_surf=label_surf, label_rect=label_rect))

        min_y = self.label_infos[0].label_rect.midleft[1]
        max_y = self.label_infos[0].label_rect.midleft[1]
        if len(self.label_infos) > 1:
            # Deconflict as needed to position each label.
            deconflicted_rects = []

            # Settings to determine how events are arranged.
            deconflict_claw = False  # If true, alternate deconflicting records up and down to keep everything more centered.
            center_new_events = False  # Whether new events should be centered vertically if possible, or continue outward.
            deconflict_up = False  # Starting deconfliction direction.

            min_top = self.label_infos[0].label_rect.top
            for li in self.label_infos:
                xss, xse, xes, xee = li.x_vals

                lr: pygame.rect.Rect = li.label_rect
                if not center_new_events:
                    lr.top = min_top
                idx = lr.collidelist(deconflicted_rects)
                while idx != -1:
                    # Find the rect we are hitting and move past it.
                    other: pygame.Rect = deconflicted_rects[idx]
                    if deconflict_up:
                        lr.bottom = other.top
                    else:
                        lr.top = other.bottom
                    idx = lr.collidelist(deconflicted_rects)
                deconflict_up = not deconflict_up if deconflict_claw else deconflict_up
                min_y = lr.midleft[1] if lr.midleft[1] < min_y else min_y
                max_y = lr.midleft[1] if lr.midleft[1] > max_y else max_y
                min_top = lr.bottom
                deconflicted_rects.append(lr)

        # Recenter the whole list of records vertically.
        v_span = max_y - min_y
        buffer = (window_height_px - v_span) / 2  # This much empty space above and below everything.
        offset = buffer - min_y  # Move records up this much to center them.
        for li in self.label_infos:
            li.label_rect.midleft = (li.label_rect.midleft[0], li.label_rect.midleft[1] + offset)
