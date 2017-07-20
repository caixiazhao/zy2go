from model.posstateinfo import PosStateInfo


class HitStateInfo(object):
    def __init__(self, atker, tgt, skill):
        self.atker = atker
        self.tgt = tgt
        self.skill = skill

    @staticmethod
    def decode(obj):
        atker = obj['atker']
        tgt = obj['tgt']
        skill = obj['skill']
        return HitStateInfo(atker, tgt, skill)