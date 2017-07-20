class PosStateInfo:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def decode(obj):
        # need parse str
        position = str(obj)
        str_pieces = position.replace("(", "").replace(")", "").replace(" ", "").split(",")
        x = str_pieces[0]
        y = str_pieces[2]
        z = str_pieces[1]
        return PosStateInfo(x, y, z)