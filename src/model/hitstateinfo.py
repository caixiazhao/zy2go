from model.posstateinfo import PosStateInfo


class HitStateInfo(object):
    def __init__(self, atker, tgt, skill):
        self.atker = atker
        self.tgt = tgt
        self.skill = skill

    def encode(self):
        json_map = {'atker': self.atker, 'tgt': self.tgt, 'skill': self.skill}
        return dict((k, v) for k, v in json_map.items() if v is not None)

    @staticmethod
    def decode(obj):
        atker = obj['atker']
        tgt = obj['tgt']
        skill = obj['skill']
        return HitStateInfo(atker, tgt, skill)