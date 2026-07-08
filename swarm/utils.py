import math

class Pose:
    def __init__(self, x, y, theta):
        self.x = x
        self.y = y
        self.theta = theta

    def __repr__(self):
        return f"Pose(x={self.x}, y={self.y}, theta={self.theta})"

    def __add__(self, other):
        return Pose(self.x + other.x, self.y + other.y, self.theta + other.theta)

    def unwrap(self):
        return self.x, self.y, self.theta

    def distance_to(self, other):
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

    def direction_to(self, other, deg):
        d = math.atan2(other.y - self.y, other.x - self.x)
        if deg:
            return math.degrees(d)
        return d
