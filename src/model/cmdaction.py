# -*- coding: utf8 -*-

# 记录选择的结果行为
# 注：skillid表示第几个skill
class CmdAction(object):
    def __init__(self, hero_name, action, skillid, tgtid, tgtpos, fwd, itemid, output_index, reward):
        self.hero_name = hero_name
        self.action = action
        self.skillid = skillid
        self.tgtid = tgtid
        self.tgtpos = tgtpos
        self.fwd = fwd
        self.itemid = itemid
        self.output_index = output_index
        self.reward = reward

    @staticmethod
    def decode(obj):
        hero_name = obj['hero_name']
        action = obj['action']
        skillid = obj['skillid'] if 'skillid' in obj else None
        tgtid = obj['tgtid'] if 'tgtid' in obj else None
        tgtpos = obj['tgtpos'] if 'tgtpos' in obj else None
        fwd = obj['fwd'] if 'fwd' in obj else None
        itemid = obj['itemid'] if 'itemid' in obj else None
        output_index = obj['output_index'] if 'output_index' in obj else None
        reward = obj['reward'] if 'reward' in obj else None
        return CmdAction(hero_name, action, skillid, tgtid, tgtpos, fwd, itemid, output_index, reward)