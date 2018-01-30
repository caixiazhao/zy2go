# -*- coding: utf8 -*-

# 记录选择的结果行为
# 注：skillid表示第几个skill
from model.fwdstateinfo import FwdStateInfo
from model.posstateinfo import PosStateInfo
class CmdAction(object):
    def __init__(self, hero_name, action, skillid, tgtid, tgtpos, fwd, itemid, output_index, reward, vpred=0, avail_action=True):
        self.hero_name = hero_name
        self.action = action
        self.skillid = str(skillid) if skillid is not None else None
        self.tgtid = str(tgtid) if tgtid is not None else None
        self.tgtpos = tgtpos
        self.fwd = fwd
        self.itemid = itemid
        self.output_index = output_index
        self.reward = reward
        self.vpred = vpred  # for ppo
        self.avail_action = avail_action

    @staticmethod
    def decode(obj):
        hero_name = obj['hero_name']
        action = obj['action']
        skillid = obj['skillid'] if 'skillid' in obj else None
        tgtid = obj['tgtid'] if 'tgtid' in obj else None
        tgtpos = PosStateInfo.decode(obj['tgtpos']) if 'tgtpos' in obj else None
        fwd = FwdStateInfo.decode(obj['fwd']) if 'fwd' in obj else None
        itemid = obj['itemid'] if 'itemid' in obj else None
        output_index = obj['output_index'] if 'output_index' in obj else None
        reward = obj['reward'] if 'reward' in obj else None
        vpred = obj['vpred'] if 'vpred' in obj else None
        return CmdAction(hero_name, action, skillid, tgtid, tgtpos, fwd, itemid, output_index, reward, vpred)

    def encode(self):
        json_map = {'hero_name': self.hero_name, 'action': self.action, 'skillid': self.skillid, 'tgtid': self.tgtid, \
                    'itemid':self.itemid, 'output_index': self.output_index, 'reward': self.reward, 'vpred': self.vpred}
        if self.tgtpos is not None:
            json_map['tgtpos'] = self.tgtpos.encode()
        if self.fwd is not None:
            json_map['fwd'] = self.fwd.encode()
        return dict((k, v) for k, v in json_map.items() if v is not None)
