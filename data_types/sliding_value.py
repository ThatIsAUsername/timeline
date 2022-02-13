
class SlidingValue:

    # How much space to cover between pos and tgt each update, percentage-wise.
    slide_factor = 0.3
    snap_distance = 0.5

    def __init__(self, start:float):
        self.pos = start
        self.tgt = start

    def set(self, target: float, snap: bool = False):
        if snap:
            self.snap(target)
        else:
            self.tgt = target

    def snap(self, target):
        self.pos = target
        self.tgt = target

    def update(self) -> float:
        """
        Move self.pos by self.slide_factor percent of the way towards self.tgt.
        If already within self.snap_distance of tgt, just snap directly there.
        Returns:
            The new self.pos
        """
        delta = self.tgt - self.pos
        if abs(delta) < self.snap_distance:
            self.snap(self.tgt)
        else:
            move_dist = delta * self.slide_factor  # How much closer to get
            self.pos += move_dist
        return self.pos

    def get(self, also_update: bool = True) -> float:
        """
        Get the current value, updating it if indicated.

        Returns:
            The current value of self.pos, moving it closer to the target if indicated.
        """
        if also_update:
            self.update()
        return self.pos

    def is_at_destination(self):
        """
        Returns: True if the value is at its target, False if it is still sliding.
        """
        return self.pos == self.tgt
