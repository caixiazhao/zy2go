class FwdStateInfo(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def to_string(self):
        return '( %s, %s, %s)' % (self.x, self.y, self.z)

    @staticmethod
    def decode(obj):
        # need parse str
        str_pieces = obj.replace("(", "").replace(")", "").replace(" ", "").split(",")
        x = str_pieces[0]
        y = str_pieces[1]
        z = str_pieces[2]
        return FwdStateInfo(x, y, z)

    def encode(self):
        return self.to_string()