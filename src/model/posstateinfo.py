from model.fwdstateinfo import FwdStateInfo


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
        x = int(str_pieces[0])
        y = int(str_pieces[1])
        z = int(str_pieces[2])
        return PosStateInfo(x, y, z)

    def encode(self):
        return self.to_string()

    def to_string(self):
        return '( %s, %s, %s)' % (self.x, self.y, self.z)

    def fwd(self, pos2):
        return FwdStateInfo(self.x-pos2.x, self.y-pos2.y, self.z-pos2.z)