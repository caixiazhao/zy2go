from model.posstateinfo import PosStateInfo


class AttackStateInfo(object):
    def __init__(self, atker, defer, tgtpos, skill):
        self.atker = atker
        self.defer = defer
        self.tgtpos = tgtpos
        self.skill = skill

    @staticmethod
    def decode(obj):
        atker = obj['atker']
        defer = obj['defer'] if 'defer' in obj else None
        tgtpos = PosStateInfo.decode(obj['tgtpos']) if 'tgtpos' in obj else None
        skill = obj['skill']
        return AttackStateInfo(atker, defer, tgtpos, skill)