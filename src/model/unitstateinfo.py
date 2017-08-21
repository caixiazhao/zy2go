# -*- coding: utf8 -*-
from fwdstateinfo import FwdStateInfo
from posstateinfo import PosStateInfo


class UnitStateInfo(object):
    def __init__(self, unit_name, state, cfg_id, pos, fwd, hp, maxhp, speed, moving, chrtype, att, attspeed,
                 mag, attpen, magpen, attpenrate, magpenrate, movelock, vis1, vis2, vis3, team):
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
        self.attspeed = attspeed
        self.mag = mag
        self.attpen = attpen
        self.magpen = magpen
        self.attpenrate = attpenrate
        self.magpenrate = magpenrate
        self.movelock = movelock
        self.vis1 = vis1
        self.vis2 = vis2
        self.vis3 = vis3
        self.team = team

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
        attspeed = delta.attspeed if delta.attspeed is not None else self.attspeed
        mag = delta.mag if delta.mag is not None else self.mag
        attpen = delta.attpen if delta.attpen is not None else self.attpen
        magpen = delta.magpen if delta.magpen is not None else self.magpen
        attpenrate = delta.attpenrate if delta.attpenrate is not None else self.attpenrate
        magpenrate = delta.magpenrate if delta.magpenrate is not None else self.magpenrate
        movelock = delta.movelock if delta.movelock is not None else self.movelock
        vis1 = delta.vis1 if delta.vis1 is not None else self.vis1
        vis2 = delta.vis2 if delta.vis2 is not None else self.vis2
        vis3 = delta.vis3 if delta.vis3 is not None else self.vis3
        team = self.team if self.team is not None else delta.team    # team信息的合并和其它的不同，会根据prev来决定，而不是根据delta
        return UnitStateInfo(unit_name, state, cfg_id, pos, fwd, hp, maxhp, speed, moving, chrtype, att,
                             attspeed, mag, attpen, magpen, attpenrate, magpenrate, movelock, vis1, vis2, vis3, team)

    def encode(self):
        json_map = {'state': self.state, 'cfgID': self.cfg_id,
                    'hp': self.hp, 'maxhp': self.maxhp, 'speed': self.speed, 'moving': self.moving, 'chrtype': self.chrtype,
                    'att': self.att, 'vis1': self.vis1, 'vis2': self.vis2,
                    'vis3': self.vis3, 'attspeed': self.attspeed, 'mag': self.mag, 'attpen': self.attpen,
                    'magpen': self.magpen,
                    'attpenrate': self.attpenrate, 'magpenrate': self.magpenrate, 'movelock': self.movelock,
                    'team': self.team
                    }
        if self.pos is not None:
            json_map['pos'] = self.pos.encode()
        if self.fwd is not None:
            json_map['fwd'] = self.fwd.encode()
        return dict((k, v) for k, v in json_map.items() if v is not None)

    def is_enemy_visible(self):
        if self.team == 0:
            return self.vis1
        else:
            return self.vis2

    @staticmethod
    def decode(obj, unit_name):
        unit_name = unit_name
        state = obj['state'] if 'state' in obj else None
        cfg_id = obj['cfgID'] if 'cfgID' in obj else None
        pos = PosStateInfo.decode(obj['pos']) if 'pos' in obj else None
        fwd = FwdStateInfo.decode(obj['fwd']) if 'fwd' in obj else None
        hp = obj['hp'] if 'hp' in obj else None
        maxhp = obj['maxhp'] if 'maxhp' in obj else None
        speed = obj['speed'] if 'speed' in obj else None
        moving = obj['moving'] if 'moving' in obj else None
        chrtype = obj['chrtype'] if 'chrtype' in obj else None
        att = obj['att'] if 'att' in obj else None
        attspeed = obj['attspeed'] if 'attspeed' in obj else None
        mag = obj['mag'] if 'mag' in obj else None
        attpen = obj['attpen'] if 'attpen' in obj else None
        magpen = obj['magpen'] if 'magpen' in obj else None
        attpenrate = obj['attpenrate'] if 'attpenrate' in obj else None
        magpenrate = obj['magpenrate'] if 'magpenrate' in obj else None
        movelock = obj['movelock'] if 'movelock' in obj else None
        vis1 = obj['vis1'] if 'vis1' in obj else None
        vis2 = obj['vis2'] if 'vis2' in obj else None
        vis3 = obj['vis3'] if 'vis3' in obj else None
        team = obj['team'] if 'team' in obj else (None if pos is None else (0 if pos.x < 0 else 1))
        return UnitStateInfo(unit_name, state, cfg_id, pos, fwd, hp, maxhp, speed, moving, chrtype, att,
                             attspeed, mag, attpen, magpen, attpenrate, magpenrate, movelock, vis1, vis2, vis3, team)
