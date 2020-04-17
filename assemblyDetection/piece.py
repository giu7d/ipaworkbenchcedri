class Piece:

    def __init__(self, corners, color, height, orientation=-1, master=0):
        self.position = -1
        self.corners = corners
        self.color = color
        self.orientation = orientation
        self.height = height
        self.matched = False
        self.master = master
