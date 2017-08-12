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
        json_map = {'ID': self.id, 'NUM': self.num}
        return dict((k, v) for k, v in json_map.items() if v is not None)
