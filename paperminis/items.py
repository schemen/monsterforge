"""
2D Item class.
This is originally from greedypacker + with an item_id added to it. A legacy requirement for monsterforge
TODO: See if we can clean this up proper and use greedypacker as is
"""


class Item:
    """
    Items class for rectangles inserted into sheets
    """

    def __init__(self, width, height, item_id,
                 CornerPoint: tuple = (0, 0),
                 rotation: bool = True) -> None:
        self.width = width
        self.height = height
        self.x = CornerPoint[0]
        self.y = CornerPoint[1]
        self.area = self.width * self.height
        self.rotated = False
        self.id = 0
        self.item_id = item_id

    def __repr__(self):
        return 'Item(width=%r, height=%r, x=%r, y=%r, id=%r)' % (self.width, self.height, self.x, self.y, self.item_id)

    def rotate(self) -> None:
        self.width, self.height = self.height, self.width
        self.rotated = False if self.rotated == True else True
