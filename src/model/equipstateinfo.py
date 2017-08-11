class EquipStateInfo:
    def __init__(self, name, id, num):
        self.name = name
        self.id = id
        self.num = num

    @staticmethod
    def decode(obj, name):
        id = obj['ID']
        num = obj['NUM']
        return EquipStateInfo(name, id, num)

    def encode(self):
        json_map = {'NAME':self.name,'ID': self.id, 'NUN': self.num}
        #json_map = {'ID': self.id, 'NUN': self.num}
        return json_map