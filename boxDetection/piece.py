class Piece:

    def __init__(self, x, y, color, orientation=None):
        self.position = -1
        self.distance = []
        self.x = x
        self.y = y
        self.color = color
        self.orientation = orientation
