from fwdstateinfo import FwdStateInfo
from posstateinfo import PosStateInfo


class UnitStateInfo(object):
    def __init__(self, unit_name, state, cfg_id, pos, fwd, hp, maxhp, speed, moving, chrtype, att):
        self.unit_name = unit_name
        self.state = state
        self.cfg_id = cfg_id
        self.pos = pos
        self.fwd = fwd
        self.hp = hp
        self.maxhp = maxhp
        self.speed = speed
        self.moving = moving
        self.chrtype = chrtype
        self.att = att

    def merge(self, delta):
        unit_name = delta.unit_name if delta.unit_name is not None else self.unit_name
        state = delta.state if delta.state is not None else self.state
        cfg_id = delta.cfg_id if delta.cfg_id is not None else self.cfg_id
        pos = delta.pos if delta.pos is not None else self.pos
        fwd = delta.fwd if delta.fwd is not None else self.fwd
        hp = delta.hp if delta.hp is not None else self.hp
        maxhp = delta.maxhp if delta.maxhp is not None else self.maxhp
        speed = delta.speed if delta.speed is not None else self.speed
        moving = delta.moving if delta.moving is not None else self.moving
        chrtype = delta.chrtype if delta.chrtype is not None else self.chrtype
        att = delta.att if delta.att is not None else self.att
        return UnitStateInfo(unit_name, state, cfg_id, pos, fwd, hp, maxhp, speed, moving, chrtype, att)

    @staticmethod
    def decode(obj, unit_name):
        unit_name = unit_name
        state = obj['state'] if 'state' in obj else ''
        cfg_id = obj['cfg_id'] if 'cfg_id' in obj else ''
        pos = PosStateInfo.decode(obj['pos']) if 'pos' in obj else ''
        fwd = FwdStateInfo.decode(obj['fwd']) if 'fwd' in obj else ''
        hp = obj['hp'] if 'hp' in obj else ''
        maxhp = obj['maxhp'] if 'maxhp' in obj else ''
        speed = obj['speed'] if 'speed' in obj else ''
        moving = obj['moving'] if 'moving' in obj else ''
        chrtype = obj['chrtype'] if 'chrtype' in obj else ''
        att = obj['att'] if 'att' in obj else ''

        return UnitStateInfo(unit_name, state, cfg_id, pos, fwd, hp, maxhp, speed, moving, chrtype, att)
